import asyncio
import logging
from os import environ
from pathlib import Path
from typing import List, Optional
import attrs

from sonic_protocol.python_parser import commands
from sonic_protocol.python_parser.answer import Answer
from sonic_protocol.python_parser.commands import Command
from sonic_protocol.schema import DeviceType
from soniccontrol.app_config import PLATFORM, SOFTWARE_VERSION
from soniccontrol.builder import DeviceBuilder
from soniccontrol.fw_device.connection import CLIConnection, Connection, SerialConnection
from soniccontrol.communication.postman_proxy_communicator import PostmanProxyCommunicator
from soniccontrol.communication.serial_communicator import SerialCommunicator
from soniccontrol.data_capturing.capture import Capture
from soniccontrol.data_capturing.capture_target import CaptureSpectrumArgs, CaptureSpectrumMeasure, CaptureTargets
from soniccontrol.data_capturing.experiment import Experiment, ExperimentMetaData
from soniccontrol.fw_device import create_connection_to_device, create_device_discovery
from soniccontrol.logger.utils import create_logger_for_connection
from soniccontrol.procedures.procedure import ProcedureArgs
from soniccontrol.procedures.procedure_controller import ProcedureController, ProcedureType
from soniccontrol.procedures.procs.spectrum_measure import SpectrumMeasureArgs
from soniccontrol.scripting.interpreter_engine import InterpreterEngine
from soniccontrol.scripting.new_scripting import NewScriptingFacade
from soniccontrol.sonic_device import SonicDevice
from soniccontrol.updater import Updater

@attrs.define()
class SpectrumArgsAdapter(CaptureSpectrumArgs):
    spectrum_args: SpectrumMeasureArgs = attrs.field() # type: ignore


class RemoteController:
    """
    The RemoteController follows a Facade pattern. It is a simple abstraction that hides the complex logic behind.
    Used for controlling the device, by sending commands, executing procedures, scripts and conducting experiments.

    Attributes
    ----------
    device_info: Info
        contains information about the device like serial number and protocol version
    protocol_consts: DeviceParamConstants
        contains the limits for protocol specific constants. Used for deducing example commands in the tests.
    """

    def __init__(self, device: SonicDevice, logger: logging.Logger):
        """
        Do not use the constructor explicitly for creating a RemoteController, 
        instead use one of the provided static connect methods
        """
        self._device: SonicDevice = device
        self._logger = logger    
        self._updater: Updater = Updater(self._device)
        self._updater.start()
        self._proc_controller: ProcedureController = ProcedureController(self._device, updater=self._updater)
        self._scripting: NewScriptingFacade = NewScriptingFacade()


    @staticmethod
    async def connect_via_serial(url: Path | str, baudrate: int = 9600, log_path: Optional[Path]=None) -> "RemoteController":
        """
        Creates a RemoteController by establishing a connection to a device over serial.

        Parameters
        ----------
        url: Path | str
            name of port to connect over. 
            Is a path on Linux, a comport on Windows
        baudrate: int, required
            baudrate for the serial connection
        log_path: Path, optional
            Used for specifying in which folder the logs should be stored

        Example
        -------
        ```
        port = "COM6"
        controller = await RemoteController.connect_via_serial(port)
        await controller.stop_running_processes() # goes out of service mode and stops procedures
        # do stuff
        await controller.disconnect()
        ```
        """
        if isinstance(url, Path):
            url = str(url)

        discovery = create_device_discovery()
        dev_info = await discovery.get_fw_device_info_of(url)
        assert dev_info is not None, "No device detected on the given port"
        connection = create_connection_to_device(dev_info, baudrate)
        return await RemoteController.connect(connection, log_path)

    @staticmethod
    async def connect_via_simulation(simulation_executable: Path, cmd_args: List[str] = [""], log_path: Optional[Path]=None) -> "RemoteController":
        return await RemoteController.connect(CLIConnection("simulation", None, simulation_executable, cmd_args), log_path)

    @staticmethod
    async def _build_device(connection: Connection, logger: logging.Logger):
        device_builder = DeviceBuilder(logger=logger)

        communicator = SerialCommunicator(logger=logger) # type: ignore
        await communicator.open_communication(connection)
        device = await device_builder.build_amp(communicator)

        return device

    @staticmethod
    async def connect(connection: Connection, log_path: Optional[Path]=None) -> "RemoteController":
        logger = create_logger_for_connection(connection.connection_name, log_path if log_path is not None else Path("."))   

        device = await RemoteController._build_device(connection, logger)
        
        controller = RemoteController(device, logger)
        
        # ensure procedures are being loaded
        await controller.load_init()

        return controller 
    
    async def connect_to_worker(self):
        """
        Connects the underlying device, if it is a postman, to the worker 
        and then returns a RemoteController, that is controls the worker (with the postman as middle man)
        
        Raises
        ------
        AssertionError
            if the underlying device is not a postman

        Returns
        -------
        worker_controller: RemoteController
            A RemoteController that controls the worker device
        """
        assert self._device.info.device_type == DeviceType.POSTMAN, "This function works only for postman devices"

        await asyncio.wait_for(self._device.wait_until_worker_connected(), 10.0)

        worker_communicator = PostmanProxyCommunicator(self._device.communicator)
        await worker_communicator.open_communication(None)
        worker_device = await DeviceBuilder(logger=self._logger).build_amp(worker_communicator)
        
        loop = asyncio.get_running_loop()
        worker_communicator.subscribe(
            worker_communicator.DISCONNECTED_EVENT, 
            lambda _: loop.run_until_complete(self._device.disconnect())
        )

        controller = RemoteController(worker_device, self._logger)

        # ensure procedures are being loaded
        await controller.load_init()

        return controller

    async def load_init(self):
        """
        This function loads procedures and other information from the device
        needed for procedure controller and other components

        Note
        ----
        This function gets called automatically when using the RemoteController.connect_* functions,
        but not when using solely the constructor.
        """
        await self._proc_controller.load_procs()

    def is_connected(self) -> bool:
        return self._device.communicator.connection_opened.is_set()

    def start_updater(self):
        """
        Starts the internal updater, that fetches periodically status information from the device.

        Note
        ----
        For running procedures, the updater needs to run. Else the controller is not able to detect anymore, when a procedure finished.
        """
        if not self._updater.running.set():
            self._updater.start()

    async def stop_updater(self):
        """
        Stops the internal updater, that fetches periodically status information from the device.

        Note
        ----
        For running procedures, the updater needs to run. Else the controller is not able to detect anymore, when a procedure finished.
        """
        if self._updater.running:
            await self._updater.stop()

    async def send_command(self, command: str | Command, raise_exception: bool = False) -> Answer:
        """
        Sends a command over the connection and waits until the device executed it. 
        It then returns the answer it received from the device.

        Parameters
        ----------
        command: str | Command, required
            The command to be executed by the device. (Plain strings can also be sent, but Command objects are the preferred way)
        raise_exception: bool, default=False
            If true, it raises and exception, if the command failed or the answer could not be validated. 
            Else it returns an Answer with the valid attribute set to False.
        
        Raises
        ------
            CommandValidationError
                if raises_exception is set to True and the received answer could not be parsed or validated
            CommandExecutionError
                If raises_exception is set to True and the device could not execute the command

        Returns
        -------
        answer: Answer
            The received answer from the device.

        Example
        -------
        ```
        # because send_command is async we have to await it. Look up asyncio for more information
        answer = await controller.send_command(cmds.SetAtf(1, 100000))
        # contains the pure str message received from the serial connection
        print(answer.message) 
        if answer.valid:
            # if the answer could be parsed and is valid, we can access the parsed fields like this
            print(answer[EFieldName.ATF]) 
        ```
        """
        if not isinstance(command, str):
            assert command != commands.GetUpdate(), "Do not send the update command directly. use the get_update() function instead"

        return await self._device.execute_command(command, raise_exception=raise_exception)
    
    async def get_update(self) -> Answer:
        """
        sends an fetch_update command to the device and returns the Answer containing the device status.

        Note
        ----
        For every device the status contains different fields. Look up in the protocol, which fields are available.
        """
        return await self._device.get_update()
    
    async def stop_running_processes(self) -> None:
        """
        Stops running processes on the device like procedures and service mode. Also turns the signal off.
        
        Note
        ----
        It is good practice to call this method always immediately after connecting to a device.
        """
        await self._device.stop_running_processes()

    async def execute_script(self, text: str) -> None:
        """
        Executes a script.

        Note
        ----
        There are examples for scripts in the script example folder and in the sonic control gui application there is a help guide for scripting.
        """
        runnable_script = self._scripting.parse_script(text)
        interpreter = InterpreterEngine(self._device, self._updater, self._logger)
        interpreter.script = runnable_script
        interpreter.start()
        await interpreter.wait_for_script_to_halt()

    def is_procedure_enabled(self, procedure: ProcedureType) -> bool:
        return procedure in self._proc_controller.proc_args_list

    def start_procedure(self, procedure: ProcedureType, args: dict | ProcedureArgs, event_loop: asyncio.AbstractEventLoop | None=None) -> None:
        """
        Starts a procedure

        Parameters
        ----------
        procedure: ProcedureType
            Specifies which procedure should run
        args: dict | ProcedureArgs
            The arguments the procedure needs. 
            The Arguments have to be valid and to be the right ones for the procedure.
            Using Procedure Args instead of dicts is the preferred way.
        event_loop: asyncio.EventLoop, optional
            The event_loop in that the procedure controller should run. Note, you have to pass nothing, 
            if this function is called from the inside of an event loop (In that case it will just use the same one).
       
        Note
        ----
        This function will start a procedure in the background. 
        When you want to halt execution, you should call wait_for_procedure_to_finish()

        Also you have to check if the procedure is enabled before starting it.
        You cannot execute disabled procedures
        """
        assert self.is_procedure_enabled(procedure), "The procedure is not enabled"

        if event_loop is None:
            event_loop = asyncio.get_running_loop()

        if isinstance(args, ProcedureArgs):
            procedure_args = args
        else:
            arg_class = self._proc_controller.proc_args_list[procedure]
            procedure_args = arg_class.from_dict(**args)

        self._proc_controller.execute_proc(procedure, procedure_args, event_loop)
        
    async def wait_for_procedure_to_finish(self):
        """
        Waits for the currently running procedure to finish.
        If no procedure runs, it returns immediately.

        Raises
        ------
        AssertionError
            If the updater is not running, because it needs that for detecting, if the procedure finished 
        """
        assert self._updater.running.is_set(), "The updater needs to be running. Else the procedure controller cannot check if a procedure finished execution"
        await self._proc_controller.wait_for_proc_to_finish()

    async def stop_procedure(self) -> None:
        """
        Stops the currently running procedure.
        Does nothing if no procedure is running.
        """
        if self._proc_controller.is_proc_running:
            await self._proc_controller.stop_proc()
        else:
            # A procedure can also be already running on the device. In that case also stop it
            await self._device.stop_procedures()

    async def measure_spectrum(self, output_dir: Path, spectrum_args: SpectrumMeasureArgs, 
                               experiment_metadata: ExperimentMetaData) -> None:
        """
        Starts a Spectrum measure, by doing that it fetches the device status for every frequency step. 
        The recorded data is stored together with the provided metadata in a experiment hdf5 file.

        Parameters
        ----------
        output_dir: Path
            Path to the directory where the experiment should be stored
        spectrum_args: SpectrumMeasureArgs
            The arguments for the Spectrum Measure to run
        experiment_meta_data: ExperimentMetaData
            Data about the setup and conduction of the experiment.
        """
        capture = Capture(output_dir)
        capture_target = CaptureSpectrumMeasure(self._updater, self._proc_controller, SpectrumArgsAdapter(spectrum_args))
        self._updater.subscribe("update", lambda e: capture.on_update(e.data["status"]))

        experiment = Experiment(experiment_metadata, self._device.info,
                                 SOFTWARE_VERSION, PLATFORM.value, 
                                 CaptureTargets.SPECTRUM_MEASURE)

        await capture.start_capture(experiment, capture_target)
        await capture.wait_for_capture_to_complete()

    async def disconnect(self) -> None:
        await self._updater.stop()
        await self._device.disconnect()

    async def restart(self) -> None:
        """
        Restarting can do that a other application is started on the device. 
        Meaning that also another protocol may be used. So references to protocol_consts and other attributes of this class
        are being invalidated by calling this function.

        Also remember to call stop_running_processes() afterwards if needed.
        """
        was_updater_running = self._updater.running.is_set()

        await self._updater.stop()
        await self._device.restart()

        connection = self._device.communicator.connection
        assert connection is not None

        if isinstance(connection, CLIConnection):
            new_connection = connection
        else:
            assert connection.dev_info is not None

            device_discovery = create_device_discovery(connection.dev_info.remote_server_url)
            new_dev_info = await device_discovery.wait_for_device_redetection(connection.dev_info, 10)
            new_connection = create_connection_to_device(new_dev_info)

        device = await self._build_device(new_connection, self._logger)
        self.__init__(device, self._logger)

        if was_updater_running:
            self.start_updater()
        else:
            await self.stop_updater()
    
    @property 
    def protocol_consts(self):
        return self._device.protocol.consts
    
    @property
    def device_info(self): 
        return self._device.info



async def main():
    import sonic_protocol.python_parser.commands as cmds
    from sonic_protocol.field_names import EFieldName

    firmware_dir_env_var = environ.get('FIRMWARE_BUILD_DIR_PATH')
    assert firmware_dir_env_var is not None
    firmware_dir = Path(firmware_dir_env_var).expanduser().resolve()
    if not firmware_dir:
        raise ValueError("Environment variable 'FIRMWARE_BUILD_DIR_PATH' is not set.")
    exe_path = firmware_dir / 'linux/platform_linux/src/device/device_main'

    controller = await RemoteController.connect_via_simulation(
        exe_path, 
        ['--profile=worker']
    )

    # it is allowed but discouraged to send strings
    answer = await controller.send_command("?protocol")
    print(answer.message)

    # use instead the cmds classes. Avoids typos and will stay compatible with future protocols
    await controller.send_command(cmds.GetProtocol())

    # ensures not procedure is running and service mode not active
    await controller.stop_running_processes() 
    answer = await controller.send_command(cmds.SetAtf(1, 100000))
    
    print(answer.message)
    if answer.valid:
        print(answer[EFieldName.ATF])

    await controller.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
