import asyncio
from os import environ
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from typing_extensions import List
from robot.api.deco import keyword, library
import robot.api.logger as logger
from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocol_list import ProtocolList
from sonic_protocol.schema import DeviceType
from sonic_robot.deduce_command_examples import deduce_command_examples
from soniccontrol.procedures.procedure_controller import ProcedureType
from soniccontrol.procedures.procs.ramper import RamperArgs
from soniccontrol.remote_controller import RemoteController
from soniccontrol_gui.plugins.device_plugin import DevicePluginRegistry, register_device_plugins


# Scope is set to suite, so that the same remote controller can be used across tests.
# This is done to reduce time needed for tests, because to build up a connection takes quite long.
@library(auto_keywords=False, scope="SUITE")
class RobotRemoteController:
    def __init__(self, log_path: Optional[str] = None):
        register_device_plugins()
        protocol_factories = { plugin.device_type: plugin.protocol_factory for plugin in DevicePluginRegistry.get_device_plugins() }
        self._controller = RemoteController(log_path=Path(log_path) if log_path else None, protocol_factories=protocol_factories)
        # Because our RemoteController is async, but robot is sync, 
        # we have to embed all the calls to the RemoteController functions into an asyncio event loop.
        self._loop = asyncio.get_event_loop()

    @keyword('Connect via serial to')
    def connect_via_serial(self, url: str) -> None:
        self._loop.run_until_complete(self._controller.connect_via_serial(Path(url)))
        logger.info(f"Connected via serial to ${url}")

    @keyword('Connect via process to')
    def connect_via_process(self, process_file: str, cmd_args: List[str] = []) -> None:
        self._loop.run_until_complete(self._controller.connect_via_process(Path(process_file), cmd_args=cmd_args))
        logger.info(f"Connected via process to ${process_file}")

    @keyword('Is connected to device')
    def is_connected(self) -> bool:
        return self._controller.is_connected()

    def _convert_answer(self, answer: Tuple[str, Dict[EFieldName, Any], bool]) -> Tuple[str, dict, bool]:
        return answer[0], { k.name: v for k, v in answer[1].items() }, answer[2]

    @keyword('Send Command ')
    def send_command(self, command_str: str) -> Tuple[str, dict, bool]:
        # if command_str == "!restart":
        #     self._loop.run_until_complete(self._controller.stop_updater())
        answer = self._loop.run_until_complete(self._controller.send_command(command_str))
        # if command_str == "!restart":
        #     self._loop.run_until_complete(self._controller.disconnect())
        return self._convert_answer(answer)

    @keyword('Deduce list of command examples')
    def deduce_command_examples(self) -> List[str]:
        assert (self._controller._device is not None)
        info = self._controller._device.info
        return deduce_command_examples(info.protocol_version, info.device_type)

    @keyword('Execute script')
    def execute_script(self, text: str) -> None:
        self._loop.run_until_complete(self._controller.execute_script(text))
    
    @keyword('Execute ramp with ')
    def execute_ramp(self, ramp_args: dict) -> None:
        self._controller.execute_ramp(RamperArgs(**ramp_args))

    @keyword('Execute procedure "${procedure}" with "${args}"')
    def execute_procedure(self, procedure: ProcedureType, args: dict) -> None:
        self._controller.execute_procedure(procedure, args)
    
    @keyword('Stop procedure')
    def stop_procedure(self) -> None:
        self._loop.run_until_complete(self._controller.stop_procedure())
    
    @keyword('Disconnect')
    def disconnect(self) -> None:
        self._loop.run_until_complete(self._controller.disconnect())

    @keyword("Sleep for ${time_ms} ms")
    def sleep(self, time_ms: int) -> None:
        """
        This is needed, because the sleep function of the robot framework pauses the whole application,
        also the execution of the asyncio event loop
        """
        self._loop.run_until_complete(asyncio.sleep(time_ms / 1000))
        print(f"Sleeping for {time_ms} ms")


def main():
    robotController = RobotRemoteController()
    #robotController.connect_via_serial("/dev/ttyUSB0")
    firmware_dir = environ.get("FIRMWARE_BUILD_DIR_PATH")
    if not firmware_dir:
        raise ValueError("Environment variable 'FIRMWARE_BUILD_DIR_PATH' is not set.")
    path = (
        firmware_dir
        + "/linux/mvp_simulation/src/simulation/cli_simulation_device/cli_simulation_device"
    )
    robotController.connect_via_process(path, ["--start-configurator"])
    print(f"Connected: {robotController.is_connected()}")
    robotController.send_command("!device=mvp_worker")
    robotController.send_command("!ramp=activated")
    robotController.send_command("!proc=ramp")
    robotController.send_command("!init_from_flash=activated")
    robotController.send_command("!service_button=activated")
    robotController.send_command("!digital_pins=deactivated")
    robotController.send_command("!digital_piano=deactivated")
    robotController.send_command("!analog=deactivated")
    robotController.send_command("!error_pin=deactivated")
    robotController.send_command("!reset_pin=deactivated")
    robotController.send_command("!save")
    robotController.send_command("!restart")
    robotController.reconnect_to_device()
    robotController.send_command("!sonic_force")
    print(robotController.send_command("-"))
    # robotController.send_command("!temperature=deactivated")
    robotController.disconnect()
    robotController.connect_via_process(path, ["--start-configurator"])

if __name__ == "__main__":
    main()