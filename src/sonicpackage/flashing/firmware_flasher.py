import pathlib
import asyncio
import subprocess
from sonicpackage import logger
from sonicpackage.interfaces import FirmwareFlasher
from sonicpackage.system import PLATFORM
import sonicpackage.bin.avrdude
from importlib import resources as rs


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
        avrdude_executable = rs.files(sonicpackage.bin.avrdude).joinpath(PLATFORM.platform_name + ".avrdude")
        return (
            f'"{str(avrdude_executable)}" '
            f'{"-n" if test_mode else ""} -v -p '
            f"atmega328p -c arduino -P {self._port} "
            f'-b 115200 -D -U flash:w:"{self._filepath}":i'
        )
    


class NewFirmwareFlasher(FirmwareFlasher):
    def __init__(self, writer: asyncio.StreamWriter | None, reader: asyncio.StreamReader | None) -> None:
        super().__init__()
        self.writer = writer
        self.reader = reader
        self.file_path = None
    
    async def flash_firmware(self) -> None:
        if self.file_path:
            _, extension = pathlib.Path(self.file_path).suffix
            if extension == ".elf" and pathlib.Path(self.file_path).exists():
                logger.info(f"Found elf file: {pathlib.Path(self.file_path).name}")


async def main() -> None:
    ff = LegacyFirmwareFlasher("COM7", "tmp.hex")
    await ff.validate_firmware()


if __name__ == "__main__":
    asyncio.run(main())
