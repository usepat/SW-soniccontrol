
import abc
import asyncio
import logging
from typing import Optional

import attrs

from sonic_protocol.python_parser.answer import Answer
from sonic_protocol.python_parser.command_deserializer import CommandDeserializer
from sonic_protocol.python_parser.commands import Command
from sonic_protocol.schema import CommandContract
from soniccontrol.communication.communicator import Communicator
from soniccontrol.communication.modbus_communicator import ModbusCommunicator
from soniccontrol.fw_device.connection import Connection

class SerialModbusConverterCommunicator(Communicator):

    _connection_opened: asyncio.Event = attrs.field(init=False, factory=asyncio.Event)
    _logger: logging.Logger = attrs.field(factory=logging.getLogger)
    _modbus_communicator: ModbusCommunicator
    _deserializer: CommandDeserializer

    def __attrs_post_init__(self) -> None:
        self._logger = logging.getLogger(
            self._logger.name + "." + SerialModbusConverterCommunicator.__name__
        )
        super().__init__()

    def __init__(self, modbus_communicator: ModbusCommunicator, deserializer: CommandDeserializer):
        self._modbus_communicator = modbus_communicator
        self._deserializer = deserializer

    @property
    def connection_opened(self) -> asyncio.Event: 
        return self._modbus_communicator.connection_opened


    @property
    def connection(self) -> Connection | None: 
        return self._modbus_communicator.connection

    async def open_communication(self, connection: Connection):
        pass

    async def close_communication(self, restart: bool = False) -> None: 
        pass

    # TODO Communicator api should take commandstructs and internally take care of serialization
    async def send_and_wait_for_response(self, request: str, **kwargs) -> str: 
        res = self._deserializer.get_command_struct(request)
        if res is not None:
            answer = await self._modbus_communicator.send_command_and_validate(res[1], res[0])
            return answer.message
        return ""


    async def read_message(self) -> str: 
        return await self._modbus_communicator.read_message()

    async def send_command_and_validate(self, command_contract: CommandContract, command: Command) -> Answer:
        """
            This command should be the only/primary api for sending commands.

            Currently only modbus uses it and for the other its not yet implement,
            so only modbus overrides it.
        """
        return await self._modbus_communicator.send_command_and_validate(command_contract, command)

    def set_device_log_handler(self, handler: logging.Handler) -> None:
        """Optional hook for installing a device log handler.

        Subclasses that have a message fetcher or device logger can override
        this to attach the provided `logging.Handler`. The default
        implementation is a no-op so callers don't need to check for support.
        """
        return None

