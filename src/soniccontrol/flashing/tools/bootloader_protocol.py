from asyncio import StreamReader, StreamWriter
import asyncio
import logging
import time
from typing import ClassVar, Optional, Tuple
import serial
import binascii
from soniccontrol.flashing.tools.utils import hex_bytes_to_int, bytes_to_little_end_uint32, little_end_uint32_to_bytes, custom_crc32
from dataclasses import dataclass, field


@dataclass
class PicoInfo:
    flash_addr: int
    flash_size: int
    erase_size: int
    write_size: int
    max_data_len: int


@dataclass
class Protocol_RP2040:
    MAX_SYNC_ATTEMPTS: ClassVar[int] = 3  # Class-level constant
    
    Opcodes: ClassVar[dict] = {
        'Sync': b'SYNC',
        'Read': b'READ',
        'Csum': b'CSUM',
        'CRC': b'CRCC',
        'Erase': b'ERAS',
        'Write': b'WRIT',
        'Seal': b'SEAL',
        'Go': b'GOGO',
        'Info': b'INFO',
        'Boot': b'BOOT',
        'ResponseSync': b'PICO',
        'ResponseSyncWota': b'WOTA',
        'ResponseOK': b'OKOK',
        'ResponseErr': b'ERR!',
    }

    _writer: StreamWriter = field(init=False)  # Instance-level fields, initialized later
    _reader: StreamReader = field(init=False)

    def __init__(self, logger: logging.Logger, writer: StreamWriter, reader: StreamReader, wait_time_before_read):
        super().__init__()
        self._logger = logging.getLogger(logger.name + "." + Protocol_RP2040.__name__)
        self._writer = writer
        self._reader = reader
        if wait_time_before_read:
            self.wait_time_before_read = wait_time_before_read

    async def write(self, data: bytes) -> bool:
        try:
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
            response = await asyncio.wait_for(self._reader.read(response_len), timeout=1.0)
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
