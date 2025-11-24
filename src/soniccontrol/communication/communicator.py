
import abc
import asyncio
import logging

from soniccontrol.communication.connection import Connection
from soniccontrol.communication.message_protocol import CommunicationProtocol
from soniccontrol.events import EventManager


class Communicator(abc.ABC, EventManager):
    DISCONNECTED_EVENT = "Disconnected"

    def __init__(self) -> None:
        super().__init__()

    @abc.abstractmethod
    def protocol(self) -> CommunicationProtocol: ...

    @property
    @abc.abstractmethod
    def connection_opened(self) -> asyncio.Event: ...

    @abc.abstractmethod
    async def open_communication(
        self, connection: Connection, baudrate: int
    ): ...

    @abc.abstractmethod
    async def close_communication(self, restart: bool = False) -> None: ...

    @abc.abstractmethod
    async def send_and_wait_for_response(self, request: str, **kwargs) -> str: ...

    @abc.abstractmethod
    async def read_message(self) -> str: ...

    @abc.abstractmethod
    async def change_baudrate(self, baudrate: int) -> None: ...

    def set_device_log_handler(self, handler: logging.Handler) -> None:
        """Optional hook for installing a device log handler.

        Subclasses that have a message fetcher or device logger can override
        this to attach the provided `logging.Handler`. The default
        implementation is a no-op so callers don't need to check for support.
        """
        return None

