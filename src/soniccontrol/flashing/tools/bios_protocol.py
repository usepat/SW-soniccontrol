from asyncio import StreamReader, StreamWriter
import asyncio
import logging
import time
from typing import ClassVar, Optional, Tuple
import serial
import binascii
from soniccontrol.flashing.tools.elf import load_elf
from soniccontrol.flashing.tools.utils import hex_bytes_to_int, bytes_to_little_end_uint32, little_end_uint32_to_bytes, custom_crc32
from dataclasses import dataclass, field
from serial_asyncio import open_serial_connection


@dataclass
class PicoInfo:
    flash_addr: int
    flash_size: int
    erase_size: int
    write_size: int
    max_data_len: int


@dataclass
class Protocol_BIOS_RP2040:
    MAX_SYNC_ATTEMPTS: ClassVar[int] = 3  # Class-level constant
    
    Opcodes: ClassVar[dict] = {
        'Sync': b'sync',
        'Read': b'read',
        'CRC': b'crc',
        'Erase': b'erase',
        'Write': b'write',
        'Seal': b'seal',
        'Go': b'gogo',
        'Info': b'info',
        'Boot': b'boot',
        'ResponseSync': b'pico',
        'ResponseOK': b'okok',
        'ResponseErr': b'error',
    }

    _writer: StreamWriter = field(init=False)  # Instance-level fields, initialized later
    _reader: StreamReader = field(init=False)
    wait_time_before_read: float = field(init=False)

    def __init__(self, logger: logging.Logger, writer: StreamWriter, reader: StreamReader, wait_time_before_read):
        super().__init__()
        self._logger = logging.getLogger(logger.name + "." + Protocol_BIOS_RP2040.__name__)
        self._writer = writer
        self._reader = reader
        if wait_time_before_read:
            self.wait_time_before_read = wait_time_before_read

    async def write(self, data: bytes) -> bool:
        try:
            await asyncio.sleep(0.2)
            self._writer.write(data)
            await self._writer.drain()
        except asyncio.TimeoutError:
            # Handle a timeout error separately
            self._logger.info(f"Writing timed out")
            return False
        
        except (OSError, IOError) as e:
            # Handle OS-level errors, often associated with disconnections or I/O issues
            self._logger.error(f"Writing failed due to I/O error: {e}")
            return False
        
        except Exception as e:
            # Catch other unexpected exceptions
            self._logger.error(f"An unexpected error occurred: {e}")
            return False
        return True
            

    async def read(self, response_len, wait_before_read = None) -> Tuple[bytes, bytes]:
        if wait_before_read:
            await asyncio.sleep(wait_before_read)
        else:
            await asyncio.sleep(self.wait_time_before_read)
        response = b""
        try:
            response = await self._reader.read(response_len)#asyncio.wait_for(self._reader.read(response_len), timeout=1.0)
        except asyncio.TimeoutError:
            pass  # Timeout means no more data, or read operation took too long
        except Exception as e:
            self._logger.info(f"{e}")
            pass
        
        err_byte = response.removeprefix(self.Opcodes["ResponseErr"])
        data_bytes = bytes()
        if len(err_byte) == response_len:
            data_bytes = response.removeprefix((self.Opcodes["ResponseOK"]))
        else:
            self._logger.info("Error encountered when reading response")
            return b"", b""
        return response, data_bytes
    
    async def flush_serial(self) -> bool:
        try:
            self._writer.write(b'\n')
            await self._writer.drain()
            await asyncio.wait_for(self._reader.read(100), timeout=1.0)
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            self._logger.info(f"Flushing failed with {e}")
            return False
        return True
            

    async def sync_cmd(self) -> bool:
        for i in range(1, self.MAX_SYNC_ATTEMPTS + 1):
            response = bytes()
            try:
                if(not await self.flush_serial()):
                    return False
                self._logger.info(f"Send sync command: {self.Opcodes['Sync']}")
                if (not await self.write(self.Opcodes["Sync"])):
                    return False
                response, _ = await self.read(4)
                self._logger.info(f"Reponse: {response}")
                if response == self.Opcodes["ResponseSync"]:
                    return True
                else:
                    self._logger.info("Sync failed")
                    
            except serial.SerialTimeoutException:
                pass
        return False

    async def info_cmd(self) -> Optional[PicoInfo]:
        expected_len = len(self.Opcodes['ResponseOK']) + (4 * 5)
        if(not await self.write(self.Opcodes["Info"])):
            return None
        _, resp_ok_bytes = await self.read(expected_len, 0.5)
        if len(resp_ok_bytes) <= 0:
            self._logger.info("Info command failed")
            return None

        flash_addr = bytes_to_little_end_uint32(resp_ok_bytes)
        flash_size = bytes_to_little_end_uint32(resp_ok_bytes[4:])
        erase_size = bytes_to_little_end_uint32(resp_ok_bytes[8:])
        write_size = bytes_to_little_end_uint32(resp_ok_bytes[12:])
        max_data_len = bytes_to_little_end_uint32(resp_ok_bytes[16:])

        self._logger.info(f"flash_addr: {flash_addr}")
        self._logger.info(f"flash_size: {flash_size}")
        self._logger.info(f"erase_size: {erase_size}")
        self._logger.info(f"write_size: {write_size}")
        self._logger.info(f"max_data_len: {max_data_len}")

        return PicoInfo(flash_addr, flash_size, erase_size, write_size, max_data_len)

    async def erase_cmd(self, addr, length) -> bool:
        expected_bit_n = 3 * 4
        write_buff = bytes()
        write_buff += self.Opcodes['Erase']
        write_buff += little_end_uint32_to_bytes(addr)
        write_buff += little_end_uint32_to_bytes(length)
        if len(write_buff) != expected_bit_n:
            missing_bits = expected_bit_n - len(write_buff)
            b = bytes(missing_bits)
            write_buff += b
        if(not await self.write(write_buff)):
            return False
        all_bytes, _ = await self.read(len(self.Opcodes['ResponseOK']))
        self._logger.info(f"Erased, response is: {all_bytes}")
        if all_bytes != self.Opcodes['ResponseOK']:
            return False
        return True

    async def write_cmd(self, addr, length, data) -> bool:
        expected_bit_n_no_data = len(self.Opcodes['Write']) + 4 + 4
        write_buff = bytes()
        write_buff += self.Opcodes['Write']
        write_buff += little_end_uint32_to_bytes(addr)
        write_buff += little_end_uint32_to_bytes(length)
        len_before_data = len(write_buff)
        if len_before_data != expected_bit_n_no_data:
            missing_bits = expected_bit_n_no_data - len_before_data
            b = bytes(missing_bits)
            write_buff += b
        write_buff += data
        if( not await self.write(write_buff)):
            return False
        all_bytes, data_bytes = await self.read(len(self.Opcodes['ResponseOK']) + 4)
        self._logger.info(f"Written, response is: {all_bytes}")
        if all_bytes == b"" or data_bytes == b"":
            return False
        resp_crc = bytes_to_little_end_uint32(data_bytes)
        calc_crc = binascii.crc32(data)

        if resp_crc != calc_crc:
            return False
        return True

    async def seal_cmd(self, addr, data) -> bool:
        expected_bits_before_crc = len(self.Opcodes['Seal']) + 4 + 4
        data_length = len(data)
        crc = binascii.crc32(data)
        write_buff = bytes()
        write_buff += self.Opcodes['Seal']
        write_buff += little_end_uint32_to_bytes(addr)
        write_buff += little_end_uint32_to_bytes(data_length)
        len_before_data = len(write_buff)
        if len_before_data != expected_bits_before_crc:
            missing_bits = expected_bits_before_crc - len_before_data
            b = bytes(missing_bits)
            write_buff += b
        write_buff += little_end_uint32_to_bytes(crc)
        if(not await self.write(write_buff)):
            return False
        all_bytes, _ = await self.read(len(self.Opcodes['ResponseOK']), 0.5)
        self._logger.info(f"Sealed, response is: {all_bytes}")
        if all_bytes[:4] != self.Opcodes['ResponseOK']:
            return False
        return True

    async def boot_cmd(self) -> bool:
        expected_bit_n = len(self.Opcodes['Boot']) + 4
        write_buff = bytes()
        write_buff += self.Opcodes['Boot']
        write_buff += little_end_uint32_to_bytes(0)
        if len(write_buff) != expected_bit_n:
            missing_bits = expected_bit_n - len(write_buff)
            b = bytes(missing_bits)
            write_buff += b
        self._logger.info(f"Send boot command: {write_buff}")
        if(not await self.write(write_buff)):
            return False
        all_bytes, _ = await self.read(len(self.Opcodes['ResponseOK']))
        self._logger.info(f"Booted, response is: {all_bytes}")
        if all_bytes == b"":
            return True
        elif all_bytes[:4] == self.Opcodes['ResponseErr']:
            return False
        self._logger.info(f"Unexpected response to boot command: {all_bytes}")
        return False
    
    async def read_until_idle(self, timeout: float = 1.0, chunk_size: int = 1024) -> bytes:
        data = bytearray()
        while True:
            try:
                chunk = await asyncio.wait_for(self._reader.read(chunk_size), timeout=timeout)
                if not chunk:
                    break  # EOF
                data.extend(chunk)
            except asyncio.TimeoutError:
                break  # no data for `timeout` seconds = idle = done
        return bytes(data)
    
    async def read_cmd(self) -> bytes:
        write_buff = bytes()
        write_buff += self.Opcodes['Read']
        self._logger.info(f"Send read command: {write_buff}")
        if(not await self.write(write_buff)):
            return bytes()
        all_bytes = await self.read_until_idle()
        self._logger.info(f"Read, response is: {all_bytes[:50]}")
        return all_bytes


def find_first_mismatch(a: bytes, b: bytes, context: int = 16):
    min_len = min(len(a), len(b))
    for i in range(min_len):
        if a[i] != b[i]:
            print(f"❌ Mismatch at byte {i}:")
            print(f"  Stored: {a[i]:02X}")
            print(f"  ELF   : {b[i]:02X}")
            # Show context
            start = max(0, i - context)
            end = min(min_len, i + context)
            print("\nContext around mismatch:")
            print("Offset  | Stored           | ELF")
            print("-----------------------------------------")
            for j in range(start, end):
                marker = " <==" if j == i else ""
                print(f"{j:06X} | {a[j]:02X}              | {b[j]:02X}{marker}")
            return i
    if len(a) != len(b):
        print(f"⚠️ Length mismatch: stored={len(a)}, elf={len(b)}")
        return min_len
    print("✅ No mismatches detected.")
    return -1


async def main():
    # Example usage
    logger = logging.getLogger("Protocol_BIOS_RP2040")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Replace with actual StreamReader and StreamWriter instances
    reader, writer = await open_serial_connection(
            url="COM23", baudrate=9600
    )

    protocol = Protocol_BIOS_RP2040(logger, writer, reader, 0.1)
    stored_bytes = await protocol.read_cmd()
    stored_hex = stored_bytes.decode('ascii')  # '00 20 04 20 F7 00 01 10 ...'
    stored_binary = bytes.fromhex(stored_hex)  # now it's real binary bytes
    img = load_elf(r"\\wsl.localhost\Ubuntu\home\usepat\GitHub\FW-sonic-firmware\build\pico\bios\tools\bootloader_new\bootloader.elf")
    # Load elf file and compare with stored bytes
    # compare storyed bytes with img.Data
    if len(stored_binary) < len(img.Data):
        logger.error(f"Stored binary is too short ({len(stored_binary)} bytes) — expected at least {len(img.Data)} bytes.")
    else:
        if stored_binary[:len(img.Data)] == img.Data:
            logger.info("Stored bytes match the ELF image data exactly (prefix match).")
        else:
            logger.warning("Mismatch detected between stored bytes and ELF image data.")
            logger.info("First 64 bytes of stored data: " + ' '.join(f'{b:02X}' for b in stored_binary[:64]))
            logger.info("First 64 bytes of ELF image:   " + ' '.join(f'{b:02X}' for b in img.Data[:64]))
            find_first_mismatch(stored_binary, img.Data)
if __name__ == "__main__":
    asyncio.run(main())