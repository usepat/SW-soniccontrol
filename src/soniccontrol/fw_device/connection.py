import abc
import asyncio
from pathlib import Path
import attrs
from typing import List, Tuple

from pymodbus import FramerType
from serial_asyncio import open_serial_connection
import logging

from sonic_protocol.protocols.protocol_v3_0_0.types.types import Parity
from soniccontrol.fw_device.fw_device_info import FwDeviceInfo
from pymodbus.client import AsyncModbusSerialClient


# TODO: implement proper factory pattern and
# close_connection should be as destructor on the connection object RAII
@attrs.define()
class Connection(abc.ABC):
    """
        Attributes
        ==========
        connection_name:
            Used for displaying purposes only

        dev_info:
            os level information about the device. It is allowed also to set this to None, 
            but in that case reconnect logic in RemoteController and DeviceWindowManager will break.
            For simulations just leave it None.
    """
    connection_name: str = attrs.field(init=True, on_setattr=None)
    dev_info: FwDeviceInfo | None = attrs.field(init=True, on_setattr=None)
    dev_info: FwDeviceInfo | None = attrs.field(init=True, on_setattr=None)
    _closed: bool = attrs.field(init=False, default=True) # maybe an asyncio event would be an even better fit here
    _lock: asyncio.Lock = attrs.field(init=False)

    @property
    def is_open(self):
        return not self._closed

    @abc.abstractmethod
    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        ...

    @abc.abstractmethod
    async def close_connection(self) -> None:
        ...

    async def open_modbus_connection(self) -> AsyncModbusSerialClient:
        raise NotImplementedError("Modbus is special")


    


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
        self._closed = False
        
        expanded_bin_file = Path(self.bin_file).expanduser().resolve()

        self.process = await asyncio.create_subprocess_exec(
            str(expanded_bin_file),
            *self.cmd_args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        assert(self.process.stdout is not None)
        assert(self.process.stdin is not None)
        
        self.process.stdin = StreamWriterWrapper(self.process.stdin)

        return self.process.stdout, self.process.stdin
    
    async def close_connection(self):     
        if self.process.returncode is not None:
            return # process already closed

        self._closed = True

        if self.process.stdin:
            self.process.stdin.close()
            await self.process.stdin.wait_closed()

        if self.process.stdout:
            # avoid blocking of the process, by reading its output in the background
            asyncio.create_task(self.process.stdout.read())

        try:
            self.process.terminate()
            await asyncio.wait_for(self.process.wait(), timeout=1)
        except asyncio.TimeoutError:
            logging.warning("Process did not respond to SIGTERM, force killing")
            self.process.kill()
            await asyncio.wait_for(self.process.wait(), timeout=1)


@attrs.define()
class SerialConnection(Connection):
    url: Path | str = attrs.field(init=True)
    baudrate: int = attrs.field(default=9600)
    writer: asyncio.StreamWriter = attrs.field(init=False)

    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        # Maybe we need to ensure here also that only one connection at a time can be open
        assert self._closed, "the last connection is still open"
        
        self._closed = False
        reader, self.writer = await open_serial_connection(
            url=str(self.url), baudrate=self.baudrate
        )
        return reader, self.writer

    async def close_connection(self):
        # use lock and bool var, to ensure the connection cannot get closed twice
        async with self._lock:
            if self._closed:
                return
            self._closed = True

            if not self.writer.is_closing():
                self.writer.close()
            await self.writer.wait_closed()

@attrs.define()
class ModbusConnection(Connection):
    url: Path | str = attrs.field(init=True)
    baudrate: int = attrs.field(default=9600)
    parity: Parity = attrs.field(default=Parity.NO)

    _client: AsyncModbusSerialClient = attrs.field(init=False)

    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        raise NotImplementedError("Can't open serial connection with modbus")

    async def close_connection(self):
        # use lock and bool var, to ensure the connection cannot get closed twice
        async with self._lock:
            if self._closed:
                return
            self._closed = True
            self._client.close()

    def parity_to_string(self) -> str:
        if self.parity == Parity.EVEN:
            return "E"
        elif self.parity == Parity.ODD:
            return "O"
        elif self.parity == Parity.NO:
            return "N"
        assert(False)

    async def open_modbus_connection(self) -> AsyncModbusSerialClient:
        assert self._closed, "the last connection is still open"
        self._closed = False
        self._client = AsyncModbusSerialClient(str(self.url), 
            baudrate=self.baudrate, 
            parity=self.parity_to_string(), 
            timeout=1.5, 
            retries=1
        )
        return self._client

async def main():
    # Replace 'cat' with the path to your actual binary, if different
    # conn = CLIConnection(bin_file=Path(os.environ["FIRMWARE_BUILD_DIR_PATH"] + "/linux/mvp_simulation/test/simulation/cli_simulation_mvp/cli_simulation_mvp"),
    #                      connection_name="cli_simulation_mvp")
    conn = SerialConnection("serial_connection", None, url="COM23", baudrate=9600)
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