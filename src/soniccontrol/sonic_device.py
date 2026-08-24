from __future__ import annotations
import asyncio
import time
from typing import List
import logging
import attrs

from sonic_protocol.command_codes import CommandCode
from sonic_protocol.field_names import BaseFieldName, EFieldName
from sonic_protocol.python_parser.answer import Answer, AnswerValidator, ValidationStatus
from sonic_protocol.python_parser.answer_validator_builder import AnswerValidatorBuilder
from sonic_protocol.python_parser.command_deserializer import CommandDeserializer
from sonic_protocol.python_parser.command_serializer import CommandSerializer
from sonic_protocol.python_parser.commands import Command, SetOff, SetOn
from sonic_protocol.schema import DeviceType, ICommandCode, Protocol, Version
from soniccontrol.communication.modbus_communicator import ModbusCommunicator
from soniccontrol.sonic_device import FirmwareInfo
from soniccontrol.communication.serial_communicator import Communicator
from sonic_protocol.python_parser import commands
from sonic_protocol.schema import DeviceType, Version


@attrs.define(auto_attribs=True)
class FirmwareInfo:
    serial_number: str = attrs.field(default="unknown")
    device_type: DeviceType = attrs.field(default=DeviceType.UNKNOWN)
    hardware_version: Version = attrs.field(default=Version(0, 0, 0), converter=Version.to_version)
    firmware_info: str = attrs.field(default="")
    firmware_version: Version = attrs.field(default=Version(0, 0, 0), converter=Version.to_version) 
    protocol_version: Version = attrs.field(default=Version(0, 0, 0), converter=Version.to_version)
    is_release: bool = attrs.field(default=True)


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
        self._modbus_operation_lock = asyncio.Lock()
        self._modbus_pending_command_count = 0

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
    
    @property
    def update_command(self) -> Command | None:
        return self._update_command

    def has_commands(self, commands: List[CommandCode | Command]) -> bool:
        return all(map(self.has_command, commands))

    def has_command(self, command: CommandCode | Command) -> bool:
        command_code = command.code if isinstance(command, Command) else command
        return command_code in self._protocol.command_contracts and self._protocol.command_contracts[command_code].command_def is not None

    def _uses_modbus(self) -> bool:
        return isinstance(self._communicator, ModbusCommunicator)

    def _has_pending_modbus_commands(self) -> bool:
        return self._modbus_pending_command_count > 0

    async def _send_command(self, command: Command, should_log: bool = True, **kwargs) -> Answer:
        command_contract = self._protocol.command_contracts.get(command.code)
        assert command_contract is not None, f"The command {command} is not known for the protocol" # throw error?
        assert command_contract.command_def is not None, f"For the command_code of {command} exists a message (notify or error), but there exists no command" 
        assert not isinstance(command_contract.command_def.sonic_text_attrs, list)

        if isinstance(self._communicator, ModbusCommunicator):
            return await self._communicator.send_command_and_validate(command_contract, command)

        request_str = self._command_serializer.serialize_command(command)
        
        answer = await self._send_message(
            request_str, 
            self._answer_validators[command.code], 
            **command_contract.command_def.sonic_text_attrs.kwargs,
            should_log=should_log,
            **kwargs,
            code=command.code  # We need this because of the legacyCommunicator since the answers of the crystal+ device don't include the commandcode. 
            #We need to remember them and prepend them to the answers
        )

        return answer

    async def _send_message(self, message: str, answer_validator: AnswerValidator| None = None, 
                            try_deduce_answer_validator: bool = False, should_log: bool = True, **kwargs) -> Answer:
        start = time.perf_counter()
        
        response_str = await self._communicator.send_and_wait_for_response(message, should_log=should_log, **kwargs)
        
        end = time.perf_counter()
        time_needed = end - start

        code: ICommandCode | None = None
        if "#" in response_str:
            code_str, response_str  = response_str.split(sep="#", maxsplit=1)
            code_int = self._protocol.convert_command_code_for_validation(int(code_str))
            code = self._protocol.command_code_cls(code_int)
            
        ERROR_CODES_START = 20000
        if code is not None and code.value >= ERROR_CODES_START:
            answer = Answer(response_str, ValidationStatus.NOT_VALID, code)
            answer.field_value_dict[EFieldName.TIMING] = time_needed
            return answer
        
        if try_deduce_answer_validator and answer_validator is None:
            command_code = self._command_deserializer.get_deserialized_command_code(message.strip())
            if command_code is not None:
                answer_validator = self._answer_validators[command_code]
        
        if answer_validator is None or not self._should_validate_answers:
            # In open rescue mode, if we cannot understand the answers of the device.
            # So in rescue mode, we skip the validation of the answers
            # Also for the serial monitor we do not want to validate answers.
            answer = Answer(response_str, ValidationStatus.NOT_CHECKED)
        else:
            answer = answer_validator.validate(response_str)
        
        answer.command_code = code
        answer.field_value_dict[EFieldName.TIMING] = time_needed
        return answer


    async def disconnect(self) -> None:
        if self._communicator.connection_opened.is_set():
            self._logger.info("Disconnect")
            await self._communicator.close_communication()

    async def _execute_command_impl(
        self,
        command: Command | str,
        should_log: bool = True,
        try_deduce_command_if_str: bool = True,
        raise_exception: bool = True,
        disconnect_on_exception: bool = True,
        warn_on_transport_error: bool = False,
        suppress_exception_log: bool = False,
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
                    should_log=should_log,
                    warn_on_transport_error=warn_on_transport_error,
                )
            else:
                answer = await self._send_command(
                    command,
                    should_log=should_log,
                    warn_on_transport_error=warn_on_transport_error,
                )
        except Exception as e:
            connection_opened = self._communicator.connection_opened.is_set()
            command_name = command if isinstance(command, str) else command.__class__.__name__
            log_fn = self._logger.warning if suppress_exception_log else self._logger.exception
            log_fn(
                "Command failed: %s (connection_opened=%s, disconnect_on_exception=%s)",
                command_name,
                connection_opened,
                disconnect_on_exception,
            )
            if disconnect_on_exception:
                await self.disconnect()

            if raise_exception:
                raise e
            return Answer(str(e), ValidationStatus.NOT_VALID)

        if raise_exception and answer.valid == ValidationStatus.NOT_VALID:
            raise CommandValidationError(answer.message)
        
        if raise_exception and answer.is_error_msg:
            raise CommandExecutionError(answer[BaseFieldName.ERROR_MESSAGE])
        
        return answer

    async def execute_command(
        self,
        command: Command | str,
        should_log: bool = True,
        try_deduce_command_if_str: bool = True,
        raise_exception: bool = True,
        disconnect_on_exception: bool = True,
        warn_on_transport_error: bool = False,
        suppress_exception_log: bool = False,
        **kwargs
    ) -> Answer:
        if not self._uses_modbus():
            return await self._execute_command_impl(
                command,
                should_log=should_log,
                try_deduce_command_if_str=try_deduce_command_if_str,
                raise_exception=raise_exception,
                disconnect_on_exception=disconnect_on_exception,
                warn_on_transport_error=warn_on_transport_error,
                suppress_exception_log=suppress_exception_log,
                **kwargs,
            )

        self._modbus_pending_command_count += 1
        max_wait_time = 30.0  # seconds
        elapsed_time = 0.0
        while self._modbus_pending_command_count > 1:
            if elapsed_time >= max_wait_time:
                self._modbus_pending_command_count -= 1
                raise TimeoutError(f"Modbus command queue timeout after {max_wait_time} seconds")
            await asyncio.sleep(0.5)
            elapsed_time += 0.5
        try:
            async with self._modbus_operation_lock:
                return await self._execute_command_impl(
                    command,
                    should_log=should_log,
                    try_deduce_command_if_str=try_deduce_command_if_str,
                    raise_exception=raise_exception,
                    disconnect_on_exception=disconnect_on_exception,
                    warn_on_transport_error=warn_on_transport_error,
                    suppress_exception_log=suppress_exception_log,
                    **kwargs,
                )
        finally:
            self._modbus_pending_command_count -= 1


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
    
    def _resolve_update_command(self) -> Command | None:
        # Let the device logic decide which command to execute for an update
        # Keep in the protocol multiple update versions for different devices,
        # instead of overriding them (to avoid breaking changes).
        if self.info.protocol_version < Version(3, 0, 0):
            return commands.GetUpdate()

        match self.info.device_type:
            case DeviceType.POSTMAN:
                return commands.GetConnectionStatus()
            case DeviceType.MVP_WORKER:
                return commands.GetUpdateWorker()
            case DeviceType.DESCALE:
                return commands.GetUpdateDescale()
            case _:
                return None
    
    async def get_update(self, raise_exception:bool=False, should_log:bool=False) -> Answer:
        if self._update_command is None:
            err_msg = "There is no update command available for this device type"
            if raise_exception:
                raise NotImplementedError(err_msg)
            else:
                return Answer(err_msg, ValidationStatus.NOT_VALID)

        if not self._uses_modbus():
            answer = await self.execute_command(self._update_command, raise_exception=raise_exception, should_log=should_log)
            if self.protocol.info.version < Version(3, 0, 0) and self.protocol.info.device_type in [DeviceType.DESCALE, DeviceType.MVP_WORKER]:
                # With a proper unit system library, we could get rid of this manual conversions 
                answer[EFieldName.URMS] = answer[EFieldName.URMS] / 1000
                answer[EFieldName.IRMS] = answer[EFieldName.IRMS] / 1000
                answer[EFieldName.TS_FLAG] = answer[EFieldName.TS_FLAG] / 1000
                phase_uV = answer[EFieldName.PHASE]
                phase_mdeg = (1800000 - phase_uV) / 10
                phase_cdeg = max(0, min(180000, phase_mdeg)) / 100
                answer[EFieldName.PHASE] = phase_cdeg
            return answer

        if self._has_pending_modbus_commands() or self._modbus_operation_lock.locked():
            return Answer("Skipped update polling while command is running", ValidationStatus.NOT_CHECKED)

        async with self._modbus_operation_lock:
            return await self._execute_command_impl(
                self._update_command,
                raise_exception=raise_exception,
                should_log=should_log,
            )

    async def stop_procedures(self):
        if self.has_command(commands.SetStop()):
            await self.execute_command(commands.SetStop(), raise_exception=False)
        elif self.has_command(commands.SetOff()):
            await self.execute_command(commands.SetOff(), raise_exception=False)

    async def stop_running_processes(self):
        """
            Goes out of service mode, stops running procedures. 
            The device will be afterwards idle and ready to accept any command.
        """
        if self.has_command(commands.SetStop()):
            await self.execute_command(commands.SetStop(), raise_exception=False)
        # We cant use SetOff for the crystal+ device because it is not ready yet
        if self.has_command(commands.SetOff()) and self.info.device_type == DeviceType.CRYSTAL:
            await self.execute_command(commands.SetOff(), raise_exception=False)
        if self.has_command(commands.SonicForce()):
            await self.execute_command(commands.SonicForce(), raise_exception=False)


    async def wait_until_worker_connected(self):
        assert self.info.device_type == DeviceType.POSTMAN, "This method only works for Postman Devices"

        while True:
            answer = await self.execute_command(commands.GetConnectionStatus())   
            if answer[EFieldName.IS_CONNECTED]:
                break         

            await asyncio.sleep(0.2)

    async def restart(self, restart_command: commands.Command = commands.RestartDevice()):
        """
        Restarts the device. 
        This class is not usable afterwards anymore, you have to create a new connection and then build a new device.
        Because the old connection may not be valid anymore (device can re enumerate on another port).

        Params
        ======
        restart_command:
            Some commands force not only a restart, but also force the device to open another application afterwards, like start_configurator
        """
        allowed_restart_commands = (commands.RestartDevice, commands.StartConfigurator, commands.StartOperator, commands.StartCustomizer, commands.StartDiagnosticsTool)
        assert isinstance(restart_command, allowed_restart_commands), "The command is not a valid restart command" 
        
        try:
            await self.execute_command(restart_command) 
        except (ConnectionError, asyncio.IncompleteReadError, CommandValidationError):
            pass # could throw a connection error, device may not respond anymore, because it is restarting
            # When using modbus the command can not be validated because the device restarts during the validation stage
        except Exception as e:
            pass
        
        try:
            await self.disconnect()
        except (TimeoutError, ConnectionError, asyncio.IncompleteReadError):
            pass # could throw a connection error, device may not respond anymore, because it is restarting
        except Exception as e:
            pass
        
