import logging
import pathlib
import asyncio
import subprocess
from typing import Optional, Tuple
from soniccontrol import logger
from soniccontrol.interfaces import FirmwareFlasher
from soniccontrol.system import PLATFORM
import soniccontrol.bin.avrdude
from importlib import resources as rs
import serial.tools.list_ports as list_ports
from serial_asyncio import open_serial_connection

from soniccontrol.flashing.tools.elf import load_elf

from soniccontrol.flashing.tools.utils import align

from soniccontrol.flashing.tools.bootloader_protocol import Protocol_RP2040


class LegacyFirmwareFlasher(FirmwareFlasher):
    def __init__(self, serial_port: str, filepath: pathlib.Path | str) -> None:
        super().__init__()
        self._port: str = serial_port
        self._filepath: pathlib.Path = (
            filepath if isinstance(filepath, pathlib.Path) else pathlib.Path(filepath)
        )
        self._file_validated: asyncio.Event = asyncio.Event()
        self._file_uploaded: asyncio.Event = asyncio.Event()

    @property
    def file_validated(self) -> asyncio.Event:
        return self._file_validated

    @property
    def file_uploaded(self) -> asyncio.Event:
        return self._file_uploaded

    async def flash_firmware(self) -> None:
        """
        Asynchronously flashes the firmware.

        This method first calls the `validate_firmware` method to validate the firmware.
        It then waits for the `file_validated` event to be set using the `wait` method.
        Finally, it calls the `upload_firmware` method to upload the firmware.
        The `file_uploaded` event is then set using the `set` method.

        Parameters:
            self (FirmwareFlasher): The instance of the FirmwareFlasher class.

        Returns:
            None: This method does not return anything.
        """
        await self.validate_firmware()
        await self._file_validated.wait()
        await self.upload_firmware()

    async def validate_firmware(self) -> None:
        """
        Validates the firmware by calling the _firmware_worker method asynchronously.
        """
        return_code, _, _ = await self._firmware_worker()
        if return_code == 0:
            logger.info("Firmware validation was successfull")
            self._file_validated.set()
        else:
            logger.error("Firmware validation failed")

    async def upload_firmware(self) -> None:
        """
        Executes the firmware upload process asynchronously.
        """
        return_code, _, _ = await self._firmware_worker(test_mode=False)
        if return_code == 0:
            logger.info("Firmware upload was successfull")
            self._file_uploaded.set()
        else:
            logger.error("Firmware upload failed")

    async def _firmware_worker(
        self, test_mode: bool = True
    ) -> tuple[int | None, str, str]:
        """
        Executes an AVRDUDE flash process asynchronously.

        Args:
            test_mode (bool, optional): A boolean indicating whether the firmware is in test mode. Defaults to True.

        Returns:
            tuple[int | None, str, str]: A tuple containing the return code, the output, and the error message.

        Raises:
            None.

        """
        logger.info(f"Starting firmware validation on {self._filepath}")

        command: str = self.flash_command(test_mode)
        process = await asyncio.create_subprocess_shell(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        out, err = await process.communicate()

        return_out: str = out.decode(PLATFORM.encoding)
        return_err: str = err.decode(PLATFORM.encoding)
        return_code: int | None = process.returncode

        logger.info(return_out)
        logger.info(return_err)

        return return_code, return_out, return_err

    def flash_command(self, test_mode: bool) -> str:
        """
        Generates the command to flash the firmware.

        Args:
            test_mode (bool): A flag indicating whether to run in test mode.

        Returns:
            str: The command to flash the firmware.

        """
        avrdude_executable = rs.files(soniccontrol.bin.avrdude).joinpath(PLATFORM.platform_name + ".avrdude")
        return (
            f'"{str(avrdude_executable)}" '
            f'{"-n" if test_mode else ""} -v -p '
            f"atmega328p -c arduino -P {self._port} "
            f'-b 115200 -D -U flash:w:"{self._filepath}":i'
        )
    


class NewFirmwareFlasher(FirmwareFlasher):
    def __init__(self, logger: logging.Logger, baudrate: int, file: pathlib.Path, wait_time_before_read = 0.01) -> None:
        super().__init__()
        self._logger = logging.getLogger(logger.name + "." + NewFirmwareFlasher.__name__)
        self.baudrate = baudrate
        self.file_path = file
        self.wait_time_before_read = wait_time_before_read

    async def find_flashable_device(self) -> Tuple[Optional[asyncio.StreamWriter], Optional[asyncio.StreamReader], Optional[str]]:
        ports = [port.device for port in list_ports.comports()]
        for port in ports:
            try:
                # Create a connection to the current port with the given baudrate
                try:
                    reader, writer = await open_serial_connection(url=port, baudrate=self.baudrate)
                except Exception as e:
                    self._logger.info(f"{e}")
                    continue
                # Flush the read buffer (read until there is nothing left, or timeout)
                try:
                    await asyncio.wait_for(reader.read(1024), timeout=2)
                except asyncio.TimeoutError:
                    pass  # If there's nothing to read, ignore the timeout and proceed

                # Send "SYNC" and try to read the response
                for attempt in range(3):  # Try this three times
                    writer.write(b'SYNC')
                    await writer.drain()

                    await asyncio.sleep(0.5)

                    try:
                        response = await asyncio.wait_for(reader.read(4), timeout=2)
                    except asyncio.TimeoutError:
                        continue  # If we timeout, go to the next port

                    if response == b'PICO':
                        # Success: Return the StreamWriter and StreamReader
                        return writer, reader, port
                    elif response == b'ERR!':
                        # If we receive "ERR!", try again by sending "SYNC"
                        continue
                    else:
                        # Unrecognized response, stop and try the next port
                        break

                # Close connection if the port didn't respond with "PICO"
                writer.close()
                await writer.wait_closed()

            except Exception as e:
                # Handle connection errors, ignore the port, and move to the next one
                print(f"Error with port {port}: {e}")
                continue
        
        # If no valid device was found, return None
        return None, None, None
    
    async def flash_firmware(self) -> bool:
        if self.file_path:
            extension = self.file_path.suffix
            if extension == ".elf" and self.file_path.exists():
                self._logger.info(f"Found elf file: {self.file_path.name}")
        else:
            self._logger.info(f"No elf file found")
            return False
        writer, reader, port = await self.find_flashable_device()
        if writer and reader:
            self._logger.info(f"Successfully found a flashable device on port {port}")
            self.img = load_elf(str(self.file_path)) # TODO change load elf to use PATH
            self._logger.info(f"Image start address: {self.img.Addr}")
            if self.img.Data is None or self.img.Addr <= -1:
                self._logger.info(f"Image empty or address incorrect")
                return False
            self.protocol = Protocol_RP2040(self._logger, writer, reader, self.wait_time_before_read)
            self._logger.info("Start erasing the flash")
            success = await self.erase_flash()
            if not success:
                self._logger.info("Error occured stop flashing")
                return False
            self._logger.info("Start flashing")
            success = await self.flash_program()
            if not success:
                self._logger.info("Error occured stop flashing")
                return False
            self._logger.info("Finish flashing by adding seal")
            success =  await self.seal_flash()
            if not success:
                self._logger.info("Error occured stop flashing")
                return False
            self._logger.info("Finished flashing, reboot device")
            success = await self.boot_into_program()
            if not success:
                self._logger.info("Error occured stop flashing")
                return False
            try:
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                self._logger.info(f"{e}")
        else:
            self._logger.info("No flashable device found")
            return False
        return True

    async def erase_flash(self) -> bool:
        retries = 0
        has_sync = await self.protocol.sync_cmd()
        if not has_sync:
            self._logger.info("Sync command failed")
            return False
        device_info = await self.protocol.info_cmd()
        if self.img.Data is not None and device_info is not None:
            pad_len = align(int(len(self.img.Data)), device_info.write_size) - int(len(self.img.Data))
            pad_zeros = bytes(pad_len)
            data = self.img.Data + pad_zeros
            if self.img.Addr < device_info.flash_addr:
                self._logger.info(f"Image load address is too low: {hex(self.img.Addr)} < {hex(device_info.flash_addr)}")

            if self.img.Addr + int(len(data)) > device_info.flash_addr + device_info.flash_size:
                self._logger.info(f"Image of {len(data)} bytes does not fit in target flash at: {hex(self.img.Addr)}")
            erase_len = int(align(len(data), device_info.erase_size))
            for start in range(0, erase_len, device_info.erase_size):
                erase_addr = self.img.Addr + start
                #debug("Erase: " + str(erase_addr) + "size: " + str(device_info.erase_size))
                has_succeeded = await self.protocol.erase_cmd(erase_addr, device_info.erase_size)
                if not has_succeeded:
                    if retries > 2:
                        self._logger.info(f"Erasing failed")
                        return False
                    retries += 1
                    self._logger.info(f"Error when erasing flash, at addr: {erase_addr}, try again")
                    start -= device_info.erase_size # Redo the step
                    has_sync = await self.protocol.sync_cmd()
                    if not has_sync:
                        self._logger.info("Sync command failed")
                        return False
                    continue
                    #puts("Error when erasing flash, at addr: " + str(erase_addr))
                    #exit_prog(True)
                else:
                    retries = 0
            return True
        return False
            
    async def  flash_program(self) -> bool:
        retries = 0
        has_sync = await self.protocol.sync_cmd()
        if not has_sync:
            self._logger.info("Sync command failed")
            return False
        device_info = await self.protocol.info_cmd()
        if self.img.Data is not None and device_info is not None:
            pad_len = align(int(len(self.img.Data)), device_info.write_size) - int(len(self.img.Data))
            pad_zeros = bytes(pad_len)
            data = self.img.Data + pad_zeros
            for start in range(0, len(data), device_info.max_data_len):
                end = start + device_info.max_data_len
                if end > int(len(data)):
                    end = int(len(data))

                wr_addr = self.img.Addr + start
                wr_len = end - start
                wr_data = data[start:end]
                crc_valid = await self.protocol.write_cmd(wr_addr, wr_len, wr_data)
                if not crc_valid:
                    if retries > 5:
                        self._logger.info(f"Flashing failed")
                        return False
                    retries += 1
                    self._logger.info(f"Error when flashing, at addr: {wr_addr}, try again")
                    start -= device_info.max_data_len # Redo the step
                    await asyncio.sleep(1)
                    has_sync = await self.protocol.sync_cmd()
                    if not has_sync:
                        self._logger.info("Sync command failed")
                        return False
                    continue
                else: 
                    retries = 0
                # puts("CRC mismatch! Exiting.")
                    #exit_prog(False)
        return True
    
    async def seal_flash(self) -> bool:
        has_sync = await self.protocol.sync_cmd()
        if not has_sync:
            self._logger.info("Sync command failed")
            return False
        device_info = await self.protocol.info_cmd()
        retries = 0
        if self.img.Data is not None and device_info is not None:
            while retries < 3:
                pad_len = align(int(len(self.img.Data)), device_info.write_size) - int(len(self.img.Data))
                pad_zeros = bytes(pad_len)
                data = self.img.Data + pad_zeros
                has_sealed = await self.protocol.seal_cmd(self.img.Addr, data)
                #debug("Has sealed: " + str(has_sealed))
                if has_sealed:
                    self._logger.info("Sealing flash finished")
                    return True
                    #puts("Sealing failed. Exiting.")
                    #exit_prog(False
                has_sync = await self.protocol.sync_cmd()
                if not has_sync:
                    self._logger.info("Sync command failed")
                    return False
                retries += 1
        self._logger.info("Sealing flash failed")
        return False

    async def boot_into_program(self) -> bool:
        has_sync = await self.protocol.sync_cmd()
        if not has_sync:
            self._logger.info("Sync command failed")
            return False
        retries = 0
        while retries < 3:
                has_booted = await self.protocol.boot_cmd()
                #debug("Has sealed: " + str(has_sealed))
                if has_booted:
                    self._logger.info("Booted successfully")
                    return True
                    #puts("Sealing failed. Exiting.")
                    #exit_prog(False
                has_sync = await self.protocol.sync_cmd()
                if not has_sync:
                    self._logger.info("Sync command failed")
                    return False
                retries += 1

        return False


async def main() -> None:
    ff = LegacyFirmwareFlasher("COM7", "tmp.hex")
    await ff.validate_firmware()


if __name__ == "__main__":
    asyncio.run(main())
