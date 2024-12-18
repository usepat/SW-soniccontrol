
import abc
import asyncio

from soniccontrol.communication.connection_factory import ConnectionFactory
from soniccontrol.communication.package_protocol import CommunicationProtocol
from soniccontrol.events import EventManager


class Communicator(abc.ABC, EventManager):
    DISCONNECTED_EVENT = "Disconnected"

    def __init__(self) -> None:
        super().__init__()

    @property 
    @abc.abstractmethod
    def writer(self) -> asyncio.StreamWriter: ...

    @property 
    @abc.abstractmethod
    def reader(self) -> asyncio.StreamReader: ...

    @property
    @abc.abstractmethod
    def protocol(self) -> CommunicationProtocol: ...

    @property
    @abc.abstractmethod
    def connection_opened(self) -> asyncio.Event: ...

    @abc.abstractmethod
    async def open_communication(
        self, connection_factory: ConnectionFactory, baudrate: int
    ): ...

    @abc.abstractmethod
    async def close_communication(self, restart: bool = False) -> None: ...

    @property
    @abc.abstractmethod
    def handshake_result(self) -> str: ...

    @abc.abstractmethod
    async def send_and_wait_for_response(self, request: str, **kwargs) -> str: ...

    @abc.abstractmethod
    async def read_message(self) -> str: ...

    @abc.abstractmethod
    async def change_baudrate(self, baudrate: int) -> None: ...