import abc
import asyncio
from pathlib import Path
import attrs
from typing import List, Tuple

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


class StreamWriterWrapper():
    """
    This class is a quick fix. 
    We have the problem, that the cli only buffers lines terminated by '\n'.
    Therefore we need to append a newline after each message.
    We could also do this in the SonicProtocol instance, but for that the device has to ignore whitespace. 
    Currently it does not support that. So this code here is needed until, the feature in the firmware is implemented.
    Also we have to consider, if we break backwards compatibility with this. So maybe this here is the best way to go.
    """
    def __init__(self, writer: asyncio.StreamWriter):
        self._writer = writer

    def write(self, data) -> None:
        self._writer.write(data)
        self._writer.write( "\n".encode())

    async def drain(self) -> None:
        await self._writer.drain()
    
    async def wait_closed(self) -> None:
        await self._writer.wait_closed()
    
    def close(self) -> None:
        self._writer.close()
    
    def is_closing(self) -> bool:
        return self._writer.is_closing()
    
    

@attrs.define()
class CLIConnection(Connection):
    bin_file: Path | str = attrs.field(init=True)
    cmd_args: List[str] = attrs.field(factory=list) 
    process: asyncio.subprocess.Process = attrs.field(init=False)     

    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        command = " ".join([str(self.bin_file), *self.cmd_args])
        self.process = await asyncio.create_subprocess_shell(
            command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        assert(self.process.stdout is not None)
        assert(self.process.stdin is not None)
        
        self.process.stdin = StreamWriterWrapper(self.process.stdin)

        return self.process.stdout, self.process.stdin
    
    async def close_connection(self):
        assert(self.process.stdin is not None)
        assert(self.process.stdout is not None)
        self.process.stdin.close()
        await self.process.stdin.wait_closed()
        # Flush output or else process can't terminate
        # Drain stdout and stderr concurrently
        await asyncio.gather(
            self.process.stdout.read(),  # or readlines()
            self.process.stderr.read() if self.process.stderr else asyncio.sleep(0),
        )
        try:
            self.process.terminate()  # or kill(), one of them
        except:
            pass

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


async def main():
    # Replace 'cat' with the path to your actual binary, if different
    # conn = CLIConnection(bin_file=Path(os.environ["FIRMWARE_BUILD_DIR_PATH"] + "/linux/mvp_simulation/test/simulation/cli_simulation_mvp/cli_simulation_mvp"),
    #                      connection_name="cli_simulation_mvp")
    conn = SerialConnection(url="COM23", baudrate=9600, connection_name="serial_connection")
    reader, writer = await conn.open_connection()
    await writer.drain()
    await asyncio.sleep(2)  # Give some time for the process to start
    try:
        test_string = "-\r"
        print(f"Sending: {test_string.strip()}")
        writer.write(test_string.encode())
        await writer.drain()

        # Read response (up to a reasonable limit)
        while True:
            response = await reader.readline()
            print(f"Received: {response.decode().strip()}")
            await asyncio.sleep(1)  # Small delay to avoid busy waiting
    finally:
        await conn.close_connection()

if __name__ == "__main__":
    asyncio.run(main())