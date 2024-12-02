import asyncio
import logging
from typing import Any, Dict

import attrs
from sonic_protocol.field_names import EFieldName
from sonic_protocol.python_parser.answer import Answer
from sonic_protocol.python_parser.commands import Command
from sonic_protocol.protocol_builder import CommandLookUpTable
from soniccontrol.command_executor import CommandExecutor
from soniccontrol.device_data import Info
from soniccontrol.interfaces import Scriptable
from soniccontrol.communication.serial_communicator import Communicator


@attrs.define(kw_only=True)
class SonicDevice(Scriptable):
    _communicator: Communicator = attrs.field()
    _logger: logging.Logger = attrs.field()
    command_executor: CommandExecutor = attrs.field(on_setattr=attrs.setters.NO_OP)
    info: Info = attrs.field(on_setattr=attrs.setters.NO_OP)
    lookup_table: CommandLookUpTable = attrs.field(on_setattr=attrs.setters.NO_OP)

    def __init__(self, communicator: Communicator, lookup_table: CommandLookUpTable, info: Info, logger: logging.Logger=logging.getLogger()) -> None:
        self.info = info
        self._logger = logging.getLogger(logger.name + "." + SonicDevice.__name__)
        self._communicator = communicator
        self.lookup_table = lookup_table
        self.command_executor = CommandExecutor(lookup_table, self._communicator)
        self._remote_proc_finished_running: asyncio.Event = asyncio.Event()

    @property
    def communicator(self) -> Communicator:
        return self._communicator

    @communicator.setter
    def communicator(self, communicator: Communicator) -> None:
        # TODO: Where the fuck do I set the communicator on the device, like this? Delete this!
        self._communicator = communicator
        self.command_executor._communicator = communicator

    def get_remote_proc_finished_event(self) -> asyncio.Event:
        return self._remote_proc_finished_running # TODO: REFACTOR THIS

    async def disconnect(self) -> None:
        if self.communicator.connection_opened.is_set():
            self._logger.info("Disconnect")
            await self.communicator.close_communication()
            del self

    async def execute_command(
        self,
        command: Command | str,
        should_log: bool = True,
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
                answer = await self.command_executor.send_message(
                    command, 
                    estimated_response_time=0.4,
                    expects_long_answer=True # kwargs needed for the old legacy communicator
                )
            else:
                answer = await self.command_executor.send_command(command)
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

