import attrs
from typing import List, Tuple
import asyncio

from soniccontrol.communication.connection import Connection
from soniccontrol.network.transport import open_remote_connection

@attrs.define()
class RemoteServerConnection(Connection):
    url: str = attrs.field(init=True)
    port: str = attrs.field(init=True)
    cmd_args: List[str] = attrs.field(factory=list) 
    baudrate: int = attrs.field(default=9600)
    _writer: asyncio.StreamWriter = attrs.field(init=False)

    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        reader, self._writer = await open_remote_connection(
            self.url, self.port, cmd_args=self.cmd_args, baudrate=self.baudrate)
        return reader, self._writer
    
    async def close_connection(self):
        self._writer.close()
        await self._writer.wait_closed()
    