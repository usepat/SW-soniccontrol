import asyncio
import logging
from soniccontrol.communication.connection import Connection
from soniccontrol.communication.message_protocol import SonicMessageProtocol
from soniccontrol.events import Event
from .serial_communicator import SerialCommunicator, Communicator
from async_tkinter_loop import async_handler

class PostmanProxyCommunicator(Communicator):
    def __init__(self, communicator: SerialCommunicator):
        self._communicator = communicator
        self._connection_opened = asyncio.Event()

        @async_handler
        async def on_disconnect(_):
            await self.close_communication()
        self._communicator.subscribe(Communicator.DISCONNECTED_EVENT, on_disconnect)

    @property
    def connection_opened(self) -> asyncio.Event: 
        return self._connection_opened

    async def open_communication(
        self, connection: Connection, baudrate: int = 0
    ): 
        assert self._communicator.connection_opened.is_set(), "cannot connect to worker, you have to connect to the postman first"
        self._connection_opened.set()

    async def close_communication(self, restart: bool = False) -> None: 
        assert not restart, "This class cannot restart the connection"

        self._connection_opened.clear()
        self.emit(Event(Communicator.DISCONNECTED_EVENT))

    async def send_and_wait_for_response(self, request: str, **kwargs) -> str: 
        return await self._communicator.send_and_wait_for_response(
            request, addr_prefix=SonicMessageProtocol.ADDR_PREFIX_WORKER, **kwargs)

    async def read_message(self) -> str: 
        """
            @note cannot differentiate between messages sent by the postman or worker.
        """
        return await self._communicator.read_message()

    def set_device_log_handler(self, handler: logging.Handler) -> None:
        """
            @note This class cannot differentiate between logs sent by the postman or worker
        """
        self._communicator.set_device_log_handler(handler)
        

