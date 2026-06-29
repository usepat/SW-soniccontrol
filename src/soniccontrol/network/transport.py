import asyncio
from typing import Any

from .client import RemoteClient, RemoteClientError


# Source - https://stackoverflow.com/a/46774855
# Posted by Vincent, modified by community. See post 'Timeline' for change history
# Retrieved 2026-03-16, License - CC BY-SA 3.0
class RemoteClientTransport(asyncio.Transport):
    def __init__(self, loop: asyncio.AbstractEventLoop, protocol: asyncio.Protocol, url: str, port: str):
        self._loop = loop
        self._protocol = protocol
        self._client = RemoteClient(url)
        self._port = port
        self._is_open = True
        self._poll_task: asyncio.Task | None = None
        self._resumed_reading = asyncio.Event()
        self._resumed_reading.set()
        super().__init__()
    
    async def start_client(self, **kwargs):
        self._client.start_session()
        await self._client.connect(self._port, **kwargs)
        self._poll_task = asyncio.Task(self._poll())

    async def _poll(self):
        while self._is_open:
            await self._resumed_reading.wait()

            data = await self._client.read(self._port)
            self._protocol.data_received(data)

    def get_protocol(self):
        return self._protocol

    def set_protocol(self, protocol):
        raise NotImplementedError()

    def is_closing(self):
        return not self._is_open

    async def _close(self):
        try:
            await self._client.disconnect(self._port)
        except RemoteClientError:
            pass # in some cases like !restart_device it can be that the device is not responsive anymore afterwards
        finally:
            await self._client.close_client()
        self._protocol.connection_lost(None)

    def close(self):
        self._is_open = False
        self._loop.create_task(self._close())
        
    def is_reading(self):
        return self._resumed_reading.is_set()

    def pause_reading(self):
        self._resumed_reading.clear()

    def resume_reading(self):
        self._resumed_reading.set()

    def get_write_buffer_size(self) -> int:
        return 0
    
    def set_write_buffer_limits(self, high=None, low=None):
        # We have no limits
        pass

    def get_write_buffer_limits(self) -> tuple[int, int]:
        return 0, 0

    def write(self, data: bytes | bytearray | memoryview):
        """Write some data bytes to the transport.

        This does not block; it buffers the data and arranges for it
        to be sent out asynchronously.
        """
        # Fuck non blocking. We ballin...
        # TODO: make this non blocking
        if isinstance(data, memoryview):
            data = data.tobytes()
        self._loop.create_task(self._client.write(self._port, bytes(data)))

    def can_write_eof(self):
        return False

    def abort(self):
        self._is_open = False
        self._loop.create_task(self._close())


async def create_remote_connection(protocol_factory, url: str, port: str, loop: asyncio.AbstractEventLoop, **kwargs):
    protocol = protocol_factory()
    transport = RemoteClientTransport(loop, protocol, url, port)
    await transport.start_client(**kwargs)
    return transport, protocol


async def open_remote_connection(url: str, port: str, loop: asyncio.AbstractEventLoop | None = None, **kwargs):
    if loop is None:
        loop = asyncio.get_running_loop()
    
    reader = asyncio.StreamReader(loop=loop)
    protocol = asyncio.StreamReaderProtocol(reader)
    factory = lambda: protocol
    transport, _ = await create_remote_connection(factory, url, port, loop, **kwargs)
    writer = asyncio.StreamWriter(transport, protocol, reader, loop)
    return reader, writer
