import logging

import attrs
from sonic_protocol.command_codes import CommandCode
from sonic_protocol.python_parser.answer import Answer, AnswerValidator
from sonic_protocol.python_parser.answer_validator_builder import AnswerValidatorBuilder
from sonic_protocol.python_parser.command_deserializer import CommandDeserializer
from sonic_protocol.python_parser.command_serializer import CommandSerializer
from sonic_protocol.python_parser.commands import Command, SetOff, SetOn
from sonic_protocol.schema import Protocol
from soniccontrol.device_data import FirmwareInfo
from soniccontrol.interfaces import Scriptable
from soniccontrol.communication.serial_communicator import Communicator


@attrs.define(kw_only=True)
class SonicDevice(Scriptable):
    communicator: Communicator = attrs.field(on_setattr=attrs.setters.NO_OP)
    _logger: logging.Logger = attrs.field()
    info: FirmwareInfo = attrs.field(on_setattr=attrs.setters.NO_OP)
    protocol: Protocol = attrs.field(on_setattr=attrs.setters.NO_OP)

    def __init__(self, communicator: Communicator, protocol: Protocol, info: FirmwareInfo, 
                 should_validate_answers: bool = True, logger: logging.Logger=logging.getLogger()) -> None:
        self.info = info
        self._logger = logging.getLogger(logger.name + "." + SonicDevice.__name__)
        self.communicator = communicator
        self.protocol = protocol
        self._answer_validators = { code: AnswerValidatorBuilder.create_answer_validator(command_contract.answer_def, protocol.field_name_cls) 
                                   for code, command_contract in self.protocol.command_contracts.items() }
        self._command_deserializer = CommandDeserializer(self.protocol)
        self._command_serializer = CommandSerializer(self.protocol)
        self._should_validate_answers = should_validate_answers

    def has_command(self, command: CommandCode | Command) -> bool:
        command_code = command.code if isinstance(command, Command) else command
        return command_code in self.protocol.command_contracts and self.protocol.command_contracts[command_code].command_def is not None

    async def _send_command(self, command: Command) -> Answer:
        command_contract = self.protocol.command_contracts.get(command.code)
        assert command_contract is not None, f"The command {command} is not known for the protocol" # throw error?
        assert command_contract.command_def is not None, f"For the command_code of {command} exists a message (notify or error), but there exists no command" 
        assert not isinstance(command_contract.command_def.sonic_text_attrs, list)

        request_str = self._command_serializer.serialize_command(command)
        
        answer = await self._send_message(
            request_str, 
            self._answer_validators[command.code], 
            **command_contract.command_def.sonic_text_attrs.kwargs,
            code=command.code  # We need this because of the legacyCommunicator since the answers of the crystal+ device don't include the commandcode. 
            #We need to remember them and prepend them to the answers
        )

        return answer

    async def _send_message(self, message: str, answer_validator: AnswerValidator| None = None, try_deduce_answer_validator: bool = False, **kwargs) -> Answer:
        response_str = await self.communicator.send_and_wait_for_response(message, **kwargs)
        
        code: CommandCode | None = None
        if "#" in response_str:
            code_str, response_str  = response_str.split(sep="#", maxsplit=1)
            code = CommandCode(int(code_str))

        ERROR_CODES_START = 20000
        if code is not None and code.value >= ERROR_CODES_START:
            return Answer(response_str, False, True, code)
        
        if try_deduce_answer_validator and answer_validator is None:
            command_code = self._command_deserializer.get_deserialized_command_code(message.strip())
            if command_code:
                answer_validator = self._answer_validators[command_code]
        
        if answer_validator is None or not self._should_validate_answers:
            # In open rescue mode, if we cannot understand the answers of the device.
            # So in rescue mode, we skip the validation of the answers
            answer = Answer(response_str, False, was_validated=False)
        else:
            answer = answer_validator.validate(response_str)
        
        answer.command_code = code
        return answer


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
                    try_deduce_answer_validator=try_deduce_command_if_str
                )
            else:
                answer = await self._send_command(command)
        except Exception as e:
            self._logger.error(e)
            await self.disconnect()
            return Answer(str(e), False, True)

        return answer


    async def set_signal_off(self) -> Answer:
        if self.has_command(SetOff()):
            return await self.execute_command(SetOff()) # We need this for legacy device
        else:
            return await self.execute_command("!OFF")

    async def set_signal_on(self) -> Answer:
        if self.has_command(SetOn()):
            return await self.execute_command(SetOn()) # We need this for legacy device
        else:
            return await self.execute_command("!ON")

    async def get_overview(self) -> Answer:
        return await self.execute_command("?")

