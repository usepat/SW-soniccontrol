import logging

import attrs
from sonic_protocol.command_codes import CommandCode
from sonic_protocol.field_names import BaseFieldName
from sonic_protocol.python_parser.answer import Answer, AnswerValidator
from sonic_protocol.python_parser.answer_validator_builder import AnswerValidatorBuilder
from sonic_protocol.python_parser.command_deserializer import CommandDeserializer
from sonic_protocol.python_parser.command_serializer import CommandSerializer
from sonic_protocol.python_parser.commands import Command, SetOff, SetOn
from sonic_protocol.schema import DeviceType, ICommandCode, Protocol
from soniccontrol.device_data import FirmwareInfo
from soniccontrol.communication.serial_communicator import Communicator
from sonic_protocol.python_parser import commands

class CommandValidationError(Exception):
    """Raised when a command's response fails validation."""
    def __init__(self, message: str):
        super().__init__(f"Validation failed: {message}")
        self.message = message

class CommandExecutionError(Exception):
    """Raised when the device returns an error message."""
    def __init__(self, error_message: str):
        super().__init__(f"Device error: {error_message}")
        self.error_message = error_message

class SonicDevice:
    def __init__(self, communicator: Communicator, protocol: Protocol, info: FirmwareInfo, 
                 should_validate_answers: bool = True, logger: logging.Logger=logging.getLogger()) -> None:
        self._info = info
        self._logger = logging.getLogger(logger.name + "." + SonicDevice.__name__)
        self._communicator = communicator
        self._protocol = protocol
        answer_validators = { code: AnswerValidatorBuilder.create_answer_validator(command_contract.answer_def, protocol.field_name_cls) 
                                   for code, command_contract in self._protocol.command_contracts.items() }
        self._answer_validators = answer_validators
        self._command_deserializer = CommandDeserializer(self._protocol)
        self._command_serializer = CommandSerializer(self._protocol)
        self._should_validate_answers = should_validate_answers

        self._update_command = self._resolve_update_command()


    @property
    def info(self) -> FirmwareInfo:
        return self._info
    
    @property
    def communicator(self) -> Communicator:
        return self._communicator
    
    @property
    def protocol(self) -> Protocol:
        return self._protocol

    def has_command(self, command: CommandCode | Command) -> bool:
        command_code = command.code if isinstance(command, Command) else command
        return command_code in self._protocol.command_contracts and self._protocol.command_contracts[command_code].command_def is not None

    async def _send_command(self, command: Command, should_log: bool = True) -> Answer:
        command_contract = self._protocol.command_contracts.get(command.code)
        assert command_contract is not None, f"The command {command} is not known for the protocol" # throw error?
        assert command_contract.command_def is not None, f"For the command_code of {command} exists a message (notify or error), but there exists no command" 
        assert not isinstance(command_contract.command_def.sonic_text_attrs, list)

        request_str = self._command_serializer.serialize_command(command)
        
        answer = await self._send_message(
            request_str, 
            self._answer_validators[command.code], 
            **command_contract.command_def.sonic_text_attrs.kwargs,
            should_log=should_log,
            code=command.code  # We need this because of the legacyCommunicator since the answers of the crystal+ device don't include the commandcode. 
            #We need to remember them and prepend them to the answers
        )

        return answer

    async def _send_message(self, message: str, answer_validator: AnswerValidator| None = None, 
                            try_deduce_answer_validator: bool = False, should_log: bool = True, **kwargs) -> Answer:
        response_str = await self._communicator.send_and_wait_for_response(message, should_log=should_log, **kwargs)
        
        code: ICommandCode | None = None
        if "#" in response_str:
            code_str, response_str  = response_str.split(sep="#", maxsplit=1)
            code = self._protocol.command_code_cls(int(code_str))

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
        if self._communicator.connection_opened.is_set():
            self._logger.info("Disconnect")
            await self._communicator.close_communication()

    async def execute_command(
        self,
        command: Command | str,
        should_log: bool = True,
        try_deduce_command_if_str: bool = True,
        raise_exception: bool = True,
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
            >>> await sonicamp.execute_command("!ON", raise_exception=True)
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
                    should_log=should_log
                )
            else:
                answer = await self._send_command(command, should_log=should_log)
        except Exception as e:
            self._logger.error(e)
            await self.disconnect()

            if raise_exception:
                raise e
            return Answer(str(e), False, True)

        if raise_exception and answer.was_validated and not answer.valid:
            raise CommandValidationError(answer.message)
        
        if raise_exception and answer.is_error_msg:
            raise CommandExecutionError(answer.field_value_dict[BaseFieldName.ERROR_MESSAGE])
        
        return answer


    async def set_signal_off(self) -> Answer:
        if self.has_command(SetOff()):
            return await self.execute_command(SetOff(), raise_exception=False) # We need this for legacy device
        else:
            return await self.execute_command("!OFF", raise_exception=False)

    async def set_signal_on(self) -> Answer:
        if self.has_command(SetOn()):
            return await self.execute_command(SetOn(), raise_exception=False) # We need this for legacy device
        else:
            return await self.execute_command("!ON", raise_exception=False)

    async def get_overview(self) -> Answer:
        return await self.execute_command("?", raise_exception=False)
    
    def _resolve_update_command(self) -> Command:
        # TODO: use different update commands  for different devices.
        match self.info.device_type:
            case DeviceType.POSTMAN:
                return commands.GetConnectionStatus()
            case _:
                return commands.GetUpdate()
    
    async def get_update(self, raise_exception:bool=False, should_log:bool=False) -> Answer:
        return await self.execute_command(self._update_command, raise_exception=raise_exception, should_log=should_log)



