import attrs
from typing import Callable, Coroutine, List, Tuple
import asyncio

from soniccontrol.communication.connection import Connection
from soniccontrol.network.client import RemoteClient
from soniccontrol.network.server import ALREADY_ACTIVE_CONNECTION_ERROR_STR
from soniccontrol.network.transport import open_remote_connection

@attrs.define()
class RemoteServerConnection(Connection):
    """
    Attributes
    ==========
    force_remove_connection:
        if True, it removes by force an already ongoing serial connection on the port we want to connect to.
        If it is a callable it calls the callable and if it returns True it removes the connection
    """
    url: str = attrs.field(init=True)
    port: str = attrs.field(init=True)
    cmd_args: List[str] = attrs.field(factory=list) 
    baudrate: int = attrs.field(default=9600)
    force_remove_connection: bool | Callable[[], Coroutine[None, None, bool]] = attrs.field(default=False)
    _writer: asyncio.StreamWriter = attrs.field(init=False)

    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:  
        client = RemoteClient(self.url)
        try:
            is_port_already_connected = client.is_port_free(self.port)
            if is_port_already_connected:
                # need to remove previous connection
                need_remove_conn = self.force_remove_connection \
                    if isinstance(self.force_remove_connection, bool) \
                    else await self.force_remove_connection()
                if need_remove_conn:
                    await client.disconnect(self.port)
        finally:
            await client.close_client()

        reader, self._writer = await open_remote_connection(
                self.url, self.port, cmd_args=self.cmd_args, baudrate=self.baudrate)
        return reader, self._writer
    
    async def close_connection(self):
        self._writer.close()
        await self._writer.wait_closed()
    