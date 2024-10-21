import abc
import asyncio
from pathlib import Path
import attrs
from typing import Tuple

from serial_asyncio import open_serial_connection

@attrs.define()
class ConnectionFactory(abc.ABC):
    # connection_name : str = attrs.field(init=True)

    @abc.abstractmethod
    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        pass

@attrs.define()
class CLIConnectionFactory(ConnectionFactory):
    bin_file: Path | str = attrs.field(init=True)

    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        process = await asyncio.create_subprocess_shell(
            str(self.bin_file),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        assert(process.stdout is not None)
        assert(process.stdin is not None)
        
        return process.stdout, process.stdin
    

@attrs.define()
class SerialConnectionFactory(ConnectionFactory):
    url: Path | str = attrs.field(init=True)
    baudrate: int = attrs.field(default=9600)

    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        reader, writer = await open_serial_connection(
            url=self.url, baudrate=self.baudrate
        )
        return reader, writer
