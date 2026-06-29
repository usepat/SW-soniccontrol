
import abc
import asyncio
import logging
from typing import Optional

from sonic_protocol.python_parser.answer import Answer
from sonic_protocol.python_parser.command_deserializer import CommandDeserializer
from sonic_protocol.python_parser.commands import Command
from sonic_protocol.schema import CommandContract
from soniccontrol.communication.communicator import Communicator
from soniccontrol.communication.modbus_communicator import ModbusCommunicator
from soniccontrol.fw_device.connection import Connection

class SerialModbusConverterCommunicator(Communicator):

    EMPTY_SUCCESS_MESSAGE = "Modbus command succeeded without textual response"
    _modbus_communicator: ModbusCommunicator
    _deserializer: CommandDeserializer

    def __init__(self, modbus_communicator: ModbusCommunicator, deserializer: CommandDeserializer):
        self._modbus_communicator = modbus_communicator
        self._deserializer = deserializer
        parent_logger = getattr(modbus_communicator, "_logger", logging.getLogger(__name__))
        self._logger = logging.getLogger(
            parent_logger.name + "." + SerialModbusConverterCommunicator.__name__
        )
        super().__init__()

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
        self._logger.debug("Serial monitor Modbus request: %s", request)
        res = self._deserializer.get_command_struct(request)
        if res is None:
            self._logger.warning(
                "Serial monitor command could not be deserialized for Modbus transport: %s",
                request,
            )
            return ""

        command, command_contract = res
        self._logger.debug(
            "Serial monitor request deserialized to %s (code=%s)",
            command,
            command_contract.code,
        )

        answer = await self._modbus_communicator.send_command_and_validate(command_contract, command)

        self._logger.debug(
            "Serial monitor Modbus answer: valid=%s, was_validated=%s, code=%s, message=%r, fields=%s",
            answer.valid,
            answer.was_validated,
            answer.command_code,
            answer.message,
            answer.field_value_dict,
        )

        if answer.valid and answer.message == "":
            self._logger.info(
                "Serial monitor Modbus command succeeded without a textual response: request=%s, fields=%s",
                request,
                answer.field_value_dict,
            )
            return self.EMPTY_SUCCESS_MESSAGE

        if not answer.valid:
            self._logger.warning(
                "Serial monitor Modbus command returned an invalid answer: request=%s, message=%r, fields=%s",
                request,
                answer.message,
                answer.field_value_dict,
            )

        return answer.message


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

