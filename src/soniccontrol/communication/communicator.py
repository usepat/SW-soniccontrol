
import abc
import asyncio
import logging

from sonic_protocol.python_parser.answer import Answer
from sonic_protocol.python_parser.commands import Command
from sonic_protocol.schema import CommandContract
from soniccontrol.fw_device.connection import Connection
from soniccontrol.communication.message_protocol import CommunicationProtocol
from soniccontrol.events import EventManager


class Communicator(abc.ABC, EventManager):
    DISCONNECTED_EVENT = "Disconnected"

    def __init__(self) -> None:
        self._connection : Connection | None = None
        super().__init__()

    @property
    @abc.abstractmethod
    def connection_opened(self) -> asyncio.Event: ...

    @property
    def connection(self) -> Connection | None: 
        return self._connection

    @abc.abstractmethod
    async def open_communication(self, connection: Connection): ...

    @abc.abstractmethod
    async def close_communication(self, restart: bool = False) -> None: ...

    @abc.abstractmethod
    async def send_and_wait_for_response(self, request: str, **kwargs) -> str: ...

    @abc.abstractmethod
    async def read_message(self) -> str: ...

    async def send_command_and_validate(self, command_contract: CommandContract, command: Command) -> Answer:
        """
            This command should be the only/primary api for sending commands.

            Currently only modbus uses it and for the other its not yet implement,
            so only modbus overrides it.
        """
        raise NotImplementedError("This api is currently only implemented in modbus")

    def set_device_log_handler(self, handler: logging.Handler) -> None:
        """Optional hook for installing a device log handler.

        Subclasses that have a message fetcher or device logger can override
        this to attach the provided `logging.Handler`. The default
        implementation is a no-op so callers don't need to check for support.
        """
        return None

