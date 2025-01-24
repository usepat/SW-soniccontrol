import logging

import attrs
from sonic_protocol.command_codes import CommandCode
from sonic_protocol.defs import CommandDef
from sonic_protocol.python_parser.answer import Answer, AnswerValidator
from sonic_protocol.python_parser.command_deserializer import CommandDeserializer
from sonic_protocol.python_parser.commands import Command
from sonic_protocol.protocol_builder import CommandLookUpTable
from soniccontrol.device_data import Info
from soniccontrol.interfaces import Scriptable
from soniccontrol.communication.serial_communicator import Communicator


@attrs.define(kw_only=True)
class SonicDevice(Scriptable):
    communicator: Communicator = attrs.field(on_setattr=attrs.setters.NO_OP)
    _logger: logging.Logger = attrs.field()
    _command_deserializer: CommandDeserializer = attrs.field()
    info: Info = attrs.field(on_setattr=attrs.setters.NO_OP)
    lookup_table: CommandLookUpTable = attrs.field(on_setattr=attrs.setters.NO_OP)

    def __init__(self, communicator: Communicator, lookup_table: CommandLookUpTable, info: Info, logger: logging.Logger=logging.getLogger()) -> None:
        self.info = info
        self._logger = logging.getLogger(logger.name + "." + SonicDevice.__name__)
        self.communicator = communicator
        self.lookup_table = lookup_table
        self._command_deserializer = CommandDeserializer(self.lookup_table)

    def has_command(self, command: CommandCode | Command) -> bool:
        if isinstance(command, Command):
            return command.code in self.lookup_table
        return command in self.lookup_table

    async def _send_command(self, command: Command) -> Answer:
        lookup_command = self.lookup_table.get(command.code)
        assert lookup_command is not None, f"The command {command} is not known for the protocol" # throw error?
        assert not isinstance(lookup_command.command_def.sonic_text_attrs, list)

        request_str = self._create_request_string(command, lookup_command.command_def)
        
        answer = await self._send_message(
            request_str, 
            lookup_command.answer_validator, 
            **lookup_command.command_def.sonic_text_attrs.kwargs
        )

        return answer

    async def _send_message(self, message: str, answer_validator: AnswerValidator| None = None, try_deduce_answer_validator: bool = False, **kwargs) -> Answer:
        response_str = await self.communicator.send_and_wait_for_response(message, **kwargs)
        
        code: CommandCode | None = None
        if "#" in response_str:
            code_str, response_str  = response_str.split(sep="#", maxsplit=1)
            code = CommandCode(int(code_str))
        
        if try_deduce_answer_validator and answer_validator is None:
            command_code = self._command_deserializer.get_deserialized_command_code(message.strip())
            if command_code:
                answer_validator = self.lookup_table[command_code].answer_validator
        
        if answer_validator is None:
            answer = Answer(response_str, False, was_validated=False)
        else:
            answer = answer_validator.validate(response_str)
        
        answer.command_code = code
        return answer

    def _create_request_string(self, command: Command, command_def: CommandDef) -> str:
        assert not isinstance(command_def.sonic_text_attrs, list)
        
        identifier = command_def.sonic_text_attrs.string_identifier
        request_msg: str = identifier[0] if isinstance(identifier, list) else identifier
        if command_def.index_param:
            assert "index"in command.args
            request_msg += str(command.args["index"])
        if command_def.setter_param:
            assert "value"in command.args 
            request_msg += "=" + str(command.args["value"])

        return request_msg


    async def disconnect(self) -> None:
        if self.communicator.connection_opened.is_set():
            self._logger.info("Disconnect")
            await self.communicator.close_communication()

    async def execute_command(
        self,
        command: Command | str,
        should_log: bool = True,
        try_deduce_command_if_str: bool = True,
        **kwargs
    ) -> Answer:
        """
        Executes a command by sending a message to the SonicDevice device and updating the status accordingly.

        Args:
            message (Union[str, Command]): The command message to execute. It can be either a string or a Command object.
            argument (Any, optional): The argument to pass to the command. Defaults to an empty string.
            **status_kwargs_if_valid_command: Additional keyword arguments to update the status if the command is valid.

        Returns:
            str: The string representation of the command's answer.

        Raises:
            Exception: If an error occurs during command execution or device disconnection.

        Note:
            - If the command is not found in the SonicDevice device's commands, it will be executed as a new command.
            - The status of the device will be updated with the command's status result and any additional status keyword arguments.
            - The command's answer will be returned as a string.

        Example:
            >>> sonicamp = SonicDevice()
            >>> await sonicamp.execute_command("power_on")
            "Device powered on."
        """
        if should_log:
            command_str = command if isinstance(command, str) else str(command.__class__)
            self._logger.info("Execute command %s", command_str)
        
        try:
            if isinstance(command, str):
                answer = await self._send_message(
                    command, 
                    try_deduce_answer_validator=try_deduce_command_if_str,
                    estimated_response_time=0.4,
                    expects_long_answer=True # kwargs needed for the old legacy communicator
                )
            else:
                answer = await self._send_command(command)
        except Exception as e:
            self._logger.error(e)
            await self.disconnect()
            return Answer(str(e), False, True)

        return answer


    async def set_signal_off(self) -> Answer:
        return await self.execute_command("!OFF")

    async def set_signal_on(self) -> Answer:
        return await self.execute_command("!ON")

    async def get_overview(self) -> Answer:
        return await self.execute_command("?")

