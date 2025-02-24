import abc
import asyncio
from pathlib import Path
import attrs
from typing import Tuple

from serial_asyncio import open_serial_connection

@attrs.define()
class Connection(abc.ABC):
    connection_name : str = attrs.field(init=True)

    @abc.abstractmethod
    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        ...

    @abc.abstractmethod
    async def close_connection(self) -> None:
        ...

@attrs.define()
class CLIConnection(Connection):
    bin_file: Path | str = attrs.field(init=True)
    process: asyncio.subprocess.Process = attrs.field(init=False)

    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        self.process = await asyncio.create_subprocess_shell(
            str(self.bin_file),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        assert(self.process.stdout is not None)
        assert(self.process.stdin is not None)
        
        return self.process.stdout, self.process.stdin
    
    async def close_connection(self):
        assert(self.process.stdin is not None)

        self.process.stdin.close()
        await self.process.stdin.wait_closed()

        self.process.terminate()
        await self.process.wait()
    

@attrs.define()
class SerialConnection(Connection):
    url: Path | str = attrs.field(init=True)
    baudrate: int = attrs.field(default=9600)
    writer: asyncio.StreamWriter = attrs.field(init=False)

    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        reader, self.writer = await open_serial_connection(
            url=str(self.url), baudrate=self.baudrate
        )
        return reader, self.writer

    async def close_connection(self):
        self.writer.close()
        await self.writer.wait_closed()