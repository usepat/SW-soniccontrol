import asyncio
import logging
from async_tkinter_loop import async_handler

from sonic_protocol.command_codes import CommandCode, ICommandCode
from soniccontrol.communication.message_protocol import SonicMessageProtocol
from soniccontrol.communication.serial_communicator import Communicator
from soniccontrol.fw_device.connection import Connection
from soniccontrol.utils.events import Event

class PostmanProxyCommunicator(Communicator):
    MAX_TIMEOUT_RETRIES = 3
    TIMEOUT_RESPONSE_MARKER = "Timeout occurred"
    WORKER_BUSY_RESPONSE_MARKER = "Cannot propagate command to subordinate, because still waiting for answer to previous command"
    RETRY_DELAY_S = 0.1
    WORKER_BUSY_RETRY_DELAY_S = 0.5
    MAX_WORKER_BUSY_WAIT_S = 120.0
    NON_IDEMPOTENT_TIMEOUT_COMMANDS = {
        CommandCode.SET_RAMP,
        CommandCode.SET_WIPE,
        CommandCode.SET_SCAN,
        CommandCode.SET_TUNE,
        CommandCode.SET_AUTO,
    }

    def __init__(self, communicator: Communicator):
        self._communicator = communicator
        self._logger = logging.getLogger(type(self).__name__)
        self._connection_opened = asyncio.Event()
        super().__init__()

        @async_handler
        async def on_disconnect(_):
            await self.close_communication()
        self._communicator.subscribe(Communicator.DISCONNECTED_EVENT, on_disconnect)
        
        if self._communicator.connection_opened.is_set():
            self._connection_opened.set()

    @property
    def connection_opened(self) -> asyncio.Event: 
        return self._connection_opened

    async def open_communication(
        self, connection: Connection | None = None
    ): 
        if connection:
            await self._communicator.open_communication(connection)        
        if self._communicator.connection_opened.is_set():
            self._connection_opened.set()

    async def close_communication(self, restart: bool = False) -> None: 
        assert not restart, "This class cannot restart the connection"

        self._connection_opened.clear()
        self.emit(Event(Communicator.DISCONNECTED_EVENT))

    async def send_and_wait_for_response(self, request: str, **kwargs) -> str: 
        # add an address prefix to all messages, so that the postman understands, it need to forward those to the worker
        response = ""
        worker_busy_deadline = None
        for attempt in range(self.MAX_TIMEOUT_RETRIES):
            response = await self._communicator.send_and_wait_for_response(
                request, addr_prefix=SonicMessageProtocol.ADDR_PREFIX_WORKER, **kwargs
            )
            if self.WORKER_BUSY_RESPONSE_MARKER in response:
                if worker_busy_deadline is None:
                    worker_busy_deadline = asyncio.get_running_loop().time() + self.MAX_WORKER_BUSY_WAIT_S

                if asyncio.get_running_loop().time() >= worker_busy_deadline:
                    return response

                self._logger.warning(
                    "Retrying Postman proxy request after busy worker response until subordinate is free: %s -> %s",
                    request,
                    response,
                )
                await asyncio.sleep(self.WORKER_BUSY_RETRY_DELAY_S)
                continue

            if self.TIMEOUT_RESPONSE_MARKER not in response:
                return response

            if attempt + 1 == self.MAX_TIMEOUT_RETRIES:
                return response

            self._logger.warning(
                "Retrying Postman proxy request after transient worker response (%d/%d): %s -> %s",
                attempt + 1,
                self.MAX_TIMEOUT_RETRIES,
                request,
                response,
            )
            await asyncio.sleep(self.RETRY_DELAY_S)

        return response

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

        

