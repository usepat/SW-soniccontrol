
import abc
import asyncio
from typing import Any, Dict

from sonicpackage.communication.connection_factory import ConnectionFactory
from sonicpackage.communication.sonicprotocol import CommunicationProtocol
from sonicpackage.events import EventManager
from sonicpackage.interfaces import Sendable


class Communicator(abc.ABC, EventManager):
    DISCONNECTED_EVENT = "Disconnected"

    def __init__(self) -> None:
        super().__init__()

    @property
    @abc.abstractmethod
    def protocol(self) -> CommunicationProtocol: ...

    @property
    @abc.abstractmethod
    def connection_opened(self) -> asyncio.Event: ...

    @abc.abstractmethod
    async def open_communication(
        self, connection_factory: ConnectionFactory
    ): ...

    @abc.abstractmethod
    async def close_communication(self) -> None: ...

    @property
    @abc.abstractmethod
    def handshake_result(self) -> Dict[str, Any]: ...

    @abc.abstractmethod
    async def send_and_wait_for_answer(self, message: Sendable) -> None: ...

    @abc.abstractmethod
    async def read_message(self) -> str: ...