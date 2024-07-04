import json
import logging
from typing import Any, Literal, Optional, Union, Iterable, Dict

import attrs
from icecream import ic
from soniccontrol.sonicpackage.amp_data import Info, Status
from soniccontrol.sonicpackage.commands import Command, CommandValidator
from soniccontrol.sonicpackage.interfaces import Scriptable
from soniccontrol.sonicpackage.procedures.script_procedures import Ramper
from soniccontrol.sonicpackage.serial_communicator import SerialCommunicator

CommandValitors = Union[CommandValidator, Iterable[CommandValidator]]

parrot_feeder = logging.getLogger("parrot_feeder")


@attrs.define(kw_only=True)
class SonicAmp(Scriptable):
    _serial: SerialCommunicator = attrs.field()
    _commands: Dict[str, Command] = attrs.field(factory=dict, converter=dict)

    _status: Status = attrs.field()
    _info: Info = attrs.field()

    @property
    def serial(self) -> SerialCommunicator:
        return self._serial

    @serial.setter
    def serial(self, serial: SerialCommunicator) -> None:
        self._serial = serial

    @property
    def commands(self) -> Dict[str, Command]:
        return self._commands

    @property
    def status(self) -> Status:
        return self._status

    @property
    def info(self) -> Info:
        return self._info

    async def disconnect(self) -> None:
        await self.serial.disconnect()
        del self

    def add_command(
        self,
        message: Union[str, Command],
        validators: Optional[CommandValitors] = None,
        **kwargs,
    ) -> None:
        """
        Adds a command to the SonicAmp object.

        Args:
            message (Union[str, Command]): The command message to add. It can be either a string or a Command object.
            validators (Optional[CommandValitors], optional): The validators to apply to the command. Defaults to None.
            **kwargs: Additional keyword arguments to pass to the Command constructor.

        Raises:
            ValueError: If the message argument is not a string or a Command object.

        Returns:
            None
        """
        if isinstance(message, Command):
            if validators is not None:
                message.add_validators(validators)
            self._commands[message.message] = message
        elif isinstance(message, str):
            self._commands[message] = Command(
                message=message, validators=validators, **kwargs
            )
        else:
            raise ValueError("Illegal Argument for message", {message})

    def add_commands(self, commands: Iterable[Command]) -> None:
        for command in commands:
            self.add_command(command)

    def has_command(self, command: Union[str, Command]) -> bool:
        return (
            self.commands.get(
                command.message if isinstance(command, Command) else command
            ) is not None
        )

    async def send_message(self, message: str = "", argument: Any = "") -> str:
        return (
            await Command(
                _serial_communication=self._serial,
                message=message,
                argument=argument,
                estimated_response_time=0.4,
                expects_long_answer=True,
            ).execute()
        )[0].string

    async def execute_command(
        self,
        message: Union[str, Command],
        argument: Any = "",
        **status_kwargs_if_valid_command,
    ) -> str:
        """
        Executes a command by sending a message to the SonicAmp device and updating the status accordingly.

        Args:
            message (Union[str, Command]): The command message to execute. It can be either a string or a Command object.
            argument (Any, optional): The argument to pass to the command. Defaults to an empty string.
            **status_kwargs_if_valid_command: Additional keyword arguments to update the status if the command is valid.

        Returns:
            str: The string representation of the command's answer.

        Raises:
            Exception: If an error occurs during command execution or device disconnection.

        Note:
            - If the command is not found in the SonicAmp device's commands, it will be executed as a new command.
            - The status of the device will be updated with the command's status result and any additional status keyword arguments.
            - The command's answer will be returned as a string.

        Example:
            >>> sonicamp = SonicAmp()
            >>> await sonicamp.execute_command("power_on")
            "Device powered on."
        """
        try:
            message = message if isinstance(message, str) else message.message
            if message not in self._commands.keys():
                ic("Command not found in commands of sonicamp", message, self)
                ic("Executing message as a new Command...")
                return await self.send_message(message=message, argument=argument)
            command: Command = self._commands[message]
            await command.execute(argument=argument, connection=self._serial)

        except Exception:
            await self.disconnect()

        await self._status.update(
            **command.status_result, **status_kwargs_if_valid_command
        )

        try:
            parrot_feeder.debug("DEVICE_STATE(%s)", json.dumps(self._status.get_dict()))
        except Exception:
            pass

        # ic(command.byte_message, command.answer, command.status_result, self._status)

        return command.answer.string

    async def set_signal_off(self) -> str:
        return await self.execute_command("!OFF", urms=0.0, irms=0.0, phase=0.0)

    async def set_signal_on(self) -> str:
        return await self.execute_command("!ON")

    async def set_signal_auto(self) -> str:
        return await self.execute_command("!AUTO")

    async def get_info(self) -> str:
        return await self.execute_command("?info")

    async def get_overview(self) -> str:
        return await self.execute_command("?")

    async def get_type(self) -> str:
        return await self.execute_command("?type")

    async def get_status(self) -> str:
        return await self.execute_command("-")

    async def get_sens(self) -> str:
        return await self.execute_command("?sens")

    async def set_serial_mode(self) -> str:
        return await self.execute_command("!SERIAL")

    async def set_analog_mode(self) -> str:
        return await self.execute_command("!ANALOG")

    async def set_frequency(self, frequency: int) -> str:
        return await self.execute_command("!f=", frequency)

    async def set_switching_frequency(self, frequency: int) -> str:
        return await self.execute_command("!swf=", frequency)

    async def set_gain(self, gain: int) -> str:
        return await self.execute_command("!g=", gain)

    async def set_relay_mode_mhz(self) -> str:
        return await self.execute_command("!MHZ")

    async def set_relay_mode_khz(self) -> str:
        return await self.execute_command("!KHZ")

    async def set_atf(self, index: int, frequency: int) -> str:
        return await self.execute_command(f"!atf{index}=", frequency)

    async def get_atf(self, index: int) -> str:
        return await self.execute_command(f"?atf{index}")

    async def set_atk(self, index: int, coefficient: float) -> str:
        return await self.execute_command(f"!atk{index}=", coefficient)

    async def set_att(self, index: int, temperature: float) -> str:
        return await self.execute_command(f"!att{index}=", temperature)

    async def get_att(self, index: int) -> str:
        return await self.execute_command(f"?att{index}")

    async def set_aton(self, index: int, time_ms: int) -> str:
        return await self.execute_command(f"!aton{index}=", time_ms)

    async def ramp_freq(
        self,
        start: int,
        stop: int,
        step: int,
        hold_on_time: float = 100,
        hold_on_unit: Literal["ms", "s"] = "ms",
        hold_off_time: float = 0,
        hold_off_unit: Literal["ms", "s"] = "ms",
    ) -> None:
        # TODO check first if self._commands contains the necessary commands to run the ramp on the device.

        return await Ramper.execute(
            self,
            lambda f: self.execute_command("!f=", f),
            (start, stop, step),
            (hold_on_time, hold_on_unit),
            (hold_off_time, hold_off_unit),
        )


