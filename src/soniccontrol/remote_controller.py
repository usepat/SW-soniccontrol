import asyncio
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from sonic_protocol.field_names import EFieldName
from sonic_protocol.python_parser.commands import Command
from soniccontrol.builder import DeviceBuilder
from soniccontrol.communication.communicator_builder import CommunicatorBuilder
from soniccontrol.communication.connection_factory import CLIConnectionFactory, ConnectionFactory, SerialConnectionFactory
from soniccontrol.logging_utils import create_logger_for_connection
from soniccontrol.procedures.procedure_controller import ProcedureController, ProcedureType
from soniccontrol.procedures.procs.ramper import RamperArgs
from soniccontrol.scripting.legacy_scripting import LegacyScriptingFacade
from soniccontrol.scripting.scripting_facade import ScriptingFacade
from soniccontrol.sonic_device import SonicDevice
from soniccontrol.updater import Updater


class RemoteController:
    NOT_CONNECTED = "Controller is not connected to a device"

    def __init__(self, log_path: Optional[Path]=None):
        self._device: Optional[SonicDevice] = None
        self._scripting: Optional[ScriptingFacade] = None
        self._proc_controller: Optional[ProcedureController] = None
        self._log_path: Optional[Path] = log_path
        self._updater: Optional[Updater] = None

    async def _connect(self, connection_factory: ConnectionFactory, connection_name: str):
        if self._log_path:
            logger = create_logger_for_connection(connection_name, self._log_path)   
        else:
            logger = create_logger_for_connection(connection_name)
        serial = await CommunicatorBuilder.build(
            connection_factory,
            logger=logger
        )
        self._device = await DeviceBuilder().build_amp(comm=serial, logger=logger)
        await self._device.communicator.connection_opened.wait()
        self._updater = Updater(self._device)
        self._updater.start()
        self._proc_controller = ProcedureController(self._device, updater=self._updater)
        self._scripting = LegacyScriptingFacade(self._device, self._proc_controller)

    async def connect_via_serial(self, url: Path, baudrate: int = 9600) -> None:
        assert self._device is None
        connection_name = url.name
        connection_factory = SerialConnectionFactory(connection_name=connection_name, url=url, baudrate=baudrate)
        await self._connect(connection_factory, connection_name)
        assert self._device is not None

    async def connect_via_process(self, process_file: Path) -> None:
        assert self._device is None
        connection_name = process_file.name
        connection_factory = CLIConnectionFactory(connection_name=connection_name, bin_file=process_file)
        await self._connect(connection_factory, connection_name)
        assert self._device is not None

    def is_connected(self) -> bool:
        return self._device is not None and self._device.communicator.connection_opened.is_set()

    def start_updater(self):
        assert self._updater is not None
        if not self._updater.running:
            self._updater.start()

    """
    Note:   
        The updater is used by the procedure controller internally 
        to get information about if a procedure is running on the device.
        If you stop the updater, the procedure controller cannot detect anymore, when a procedure is finished and will run forever. 
        However you can manually pull an update over the updater and send that to the procedure controller or just
        call stop procedure.
    """
    async def stop_updater(self):
        assert self._updater is not None
        if self._updater.running:
            await self._updater.stop()

    async def send_command(self, command: str | Command) -> Tuple[str, Dict[EFieldName, Any], bool]:
        assert self._device is not None,    RemoteController.NOT_CONNECTED
        answer = await self._device.execute_command(command)
        return answer.message, answer.field_value_dict, answer.valid

    async def execute_script(self, text: str) -> None:
        assert self._device is not None,    RemoteController.NOT_CONNECTED
        assert self._scripting is not None

        interpreter = self._scripting.parse_script(text)
        async for line_index, task in interpreter:
            pass

    def execute_ramp(self, ramp_args: RamperArgs) -> None:
        assert self._device is not None,    RemoteController.NOT_CONNECTED
        assert self._proc_controller is not None

        self._proc_controller.execute_proc(ProcedureType.RAMP, ramp_args)

    def execute_procedure(self, procedure: ProcedureType, args: dict) -> None:
        assert self._device is not None,    RemoteController.NOT_CONNECTED
        assert self._proc_controller is not None

        arg_class = self._proc_controller.proc_args_list[procedure]
        procedure_args = arg_class(args)
        self._proc_controller.execute_proc(procedure, procedure_args)

    async def stop_procedure(self) -> None:
        assert self._device is not None,    RemoteController.NOT_CONNECTED
        assert self._proc_controller is not None

        await self._proc_controller.stop_proc()
    
    async def disconnect(self) -> None:
        if self._updater is not None:
            await self._updater.stop()
            self._updater = None

        if self._device is not None:
            await self._device.disconnect()
            self._scripting = None
            self._proc_controller = None
            self._device = None

        assert self._device is None
        assert self._updater is None



from soniccontrol.remote_controller import RemoteController
import sonic_protocol.python_parser.commands as cmds
from sonic_protocol.field_names import EFieldName

async def main():
    controller = RemoteController()
    await controller.connect_via_serial(Path("/dev/ttyUSB0"))

    answer_str, _, _ = await controller.send_command("?protocol")
    answer_str, _, _ = await controller.send_command(cmds.GetProtocol())
    answer_str, answer_dict, is_valid = await controller.send_command(cmds.SetAtf(1, 100000))
    
    print(answer_str)
    if is_valid:
        print(answer_dict[EFieldName.ATF])

    await controller.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
