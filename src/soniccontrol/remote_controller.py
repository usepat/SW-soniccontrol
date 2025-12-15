import asyncio
from os import environ
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import attrs

from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocol_list import ProtocolList
from sonic_protocol.python_parser.commands import Command
from sonic_protocol.schema import DeviceType
from soniccontrol.app_config import PLATFORM, SOFTWARE_VERSION
from soniccontrol.builder import DeviceBuilder
from soniccontrol.communication.connection import CLIConnection, Connection, SerialConnection
from soniccontrol.data_capturing.capture import Capture
from soniccontrol.data_capturing.capture_target import CaptureSpectrumArgs, CaptureSpectrumMeasure, CaptureTargets
from soniccontrol.data_capturing.experiment import Experiment, ExperimentMetaData
from soniccontrol.logging_utils import create_logger_for_connection
from soniccontrol.procedures.procedure_controller import ProcedureController, ProcedureType
from soniccontrol.procedures.procs.spectrum_measure import SpectrumMeasureArgs
from soniccontrol.scripting.interpreter_engine import InterpreterEngine
from soniccontrol.scripting.new_scripting import NewScriptingFacade
from soniccontrol.scripting.scripting_facade import ScriptingFacade
from soniccontrol.sonic_device import SonicDevice
from soniccontrol.updater import Updater

@attrs.define()
class SpectrumArgsAdapter(CaptureSpectrumArgs):
    spectrum_args: SpectrumMeasureArgs = attrs.field() # type: ignore


class RemoteController:
    NOT_CONNECTED = "Controller is not connected to a device"

    def __init__(self, log_path: Optional[Path]=None, protocol_factories: Dict[DeviceType, ProtocolList] = {}):
        self._device: Optional[SonicDevice] = None
        self._scripting: Optional[ScriptingFacade] = None
        self._proc_controller: Optional[ProcedureController] = None
        self._log_path: Optional[Path] = log_path
        self._updater: Optional[Updater] = None
        self._protocol_factories = protocol_factories

    # TODO: make the connect functions classmethods and they give back a RemoteController
    async def _connect(self, connection: Connection, connection_name: str):
        if self._log_path:
            self._logger = create_logger_for_connection(connection_name, self._log_path)   
        else:
            self._logger = create_logger_for_connection(connection_name)

        self._device = await DeviceBuilder(logger=self._logger, protocol_factories=self._protocol_factories).build_amp(connection)
        self._updater = Updater(self._device)
        self._updater.start()
        self._proc_controller = ProcedureController(self._device, updater=self._updater)
        self._scripting = NewScriptingFacade()

    async def connect_via_serial(self, url: Path, baudrate: int = 9600) -> None:
        assert self._device is None
        connection_name = url.name
        connection = SerialConnection(connection_name=connection_name, url=url, baudrate=baudrate)
        await self._connect(connection, connection_name)
        assert self._device is not None

    async def connect_via_process(self, process_file: Path, cmd_args: List[str] = []) -> None:
        assert self._device is None
        connection_name = process_file.name
        connection = CLIConnection(connection_name=connection_name, bin_file=process_file, cmd_args=cmd_args)
        await self._connect(connection, connection_name)
        assert self._device is not None

    def is_connected(self) -> bool:
        return self._device is not None and self._device.communicator.connection_opened.is_set()

    def start_updater(self):
        assert self._updater is not None
        if not self._updater.running.set():
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
        answer = await self._device.execute_command(command, raise_exception=False)
        answer.field_value_dict[EFieldName.COMMAND_CODE] = answer.command_code # TODO you gotta do better senator
        return answer.message, answer.field_value_dict, answer.valid

    async def execute_script(self, text: str, callback: Callable[[str], None] = lambda _: None) -> None:
        assert self._device is not None,    RemoteController.NOT_CONNECTED
        assert self._scripting is not None
        assert self._updater is not None
        assert self._proc_controller is not None

        runnable_script = self._scripting.parse_script(text)
        interpreter = InterpreterEngine(self._device, self._updater, self._logger)
        interpreter.subscribe_property_listener(InterpreterEngine.PROPERTY_CURRENT_TARGET, lambda target: callback(target.data.task))
        interpreter.script = runnable_script
        interpreter.start()
        await interpreter.wait_for_script_to_halt()

    def execute_procedure(self, procedure: ProcedureType, args: dict, event_loop=asyncio.get_event_loop()) -> None:
        assert self._device is not None,    RemoteController.NOT_CONNECTED
        assert self._proc_controller is not None

        arg_class = self._proc_controller.proc_args_list[procedure]
        procedure_args = arg_class.from_dict(**args)
        self._proc_controller.execute_proc(procedure, procedure_args, event_loop)
        
    async def wait_for_procedure_to_finish(self):
        assert self._proc_controller is not None
        assert self._updater
        assert self._updater.running

        await self._proc_controller.wait_for_proc_to_finish()

    async def stop_procedure(self) -> None:
        assert self._device is not None,    RemoteController.NOT_CONNECTED
        assert self._proc_controller is not None

        await self._proc_controller.stop_proc()

    async def measure_spectrum(self, output_dir: Path, spectrum_args: SpectrumMeasureArgs, 
                               experiment_metadata: ExperimentMetaData, blocking: bool=True) -> None:
        assert self._device is not None,    RemoteController.NOT_CONNECTED
        assert self._updater
        assert self._proc_controller


        capture = Capture(output_dir)
        capture_target = CaptureSpectrumMeasure(self._updater, self._proc_controller, SpectrumArgsAdapter(spectrum_args))
        self._updater.subscribe("update", lambda e: capture.on_update(e.data["status"]))

        experiment = Experiment(experiment_metadata, self._device.info,
                                 SOFTWARE_VERSION, PLATFORM.value, 
                                 CaptureTargets.SPECTRUM_MEASURE)

        await capture.start_capture(experiment, capture_target)
        if blocking:
            await capture.wait_for_capture_to_complete()

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
        #
    
    @property
    def updater(self):
        assert self._updater
        return self._updater
    
    @property 
    def protocol_consts(self):
        assert self._device
        return self._device.protocol.consts



async def main():
    from soniccontrol.remote_controller import RemoteController
    import sonic_protocol.python_parser.commands as cmds
    from sonic_protocol.field_names import EFieldName

    controller = RemoteController()
    #await controller.connect_via_serial(Path("/dev/ttyUSB0"))
    firmware_dir = environ.get('FIRMWARE_BUILD_DIR_PATH')
    if not firmware_dir:
        raise ValueError("Environment variable 'FIRMWARE_BUILD_DIR_PATH' is not set.")
    exe_path = firmware_dir + '/linux/platform_linux/src/device/device_main'
    await controller.connect_via_process(Path(exe_path), [
        '--product-type=worker', 
        '--name=test_worker', 
        '--port=4000', 
        f'--data-dir={firmware_dir + "/data"}'
    ])
    answer_str, _, _ = await controller.send_command("?protocol")
    answer_str, _, _ = await controller.send_command(cmds.GetProtocol())
    answer_str, answer_dict, is_valid = await controller.send_command(cmds.SetAtf(1, 100000))
    
    print(answer_str)
    if is_valid:
        print(answer_dict[EFieldName.ATF])

    await controller.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
