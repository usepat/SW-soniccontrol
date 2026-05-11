from pathlib import Path
from typing import List
import pytest
import pytest_asyncio
from sonic_protocol.protocols.protocol_v3_0_0.types.types import Parity
from sonic_protocol.schema import ControlMode, DeviceParamConstants, Loglevel
from soniccontrol import DeviceParamConstantType
from sonic_protocol.python_parser import commands
from soniccontrol.fw_device.connection import CLIConnection, ModbusConnection
from soniccontrol.fw_device import create_connection_to_device, create_device_discovery
from soniccontrol import RemoteController, DeviceType
from sonic_pytest.plugin import SonicControlPlugin, create_worker_process_impl


create_worker_process = pytest_asyncio.fixture(create_worker_process_impl, scope="package", loop_scope="package")


async def reset_remote_controller_state(remote_controller: RemoteController) -> None:
    await remote_controller.send_command(commands.SetLogLevel("global", Loglevel.ERROR))
    await remote_controller.send_command(commands.SetControlMode(ControlMode.REMOTE))
    await remote_controller.send_command(commands.ClearErrors())
    await remote_controller.send_command(commands.SonicForce())
    await remote_controller.send_command(commands.SetStop())
    await remote_controller.send_command(commands.SetOff())


def resolve_protocol_arg(arg, consts: DeviceParamConstants | None = None):
    if consts is None:
        return arg
    if isinstance(arg, DeviceParamConstantType):
        return getattr(consts, arg.value)
    return arg


async def create_connection(plugin_config: SonicControlPlugin, data_dir: Path | None, simulation_args: List[str] = []):
    is_simulation: bool = plugin_config.is_simulation
    device_type: DeviceType = plugin_config.device_type
    serial_port: str | None = plugin_config.serial_port
    modbus_serial_port: str | None = plugin_config.modbus_serial_port
    remote_server_url: str | None = plugin_config.remote_server_url

    if is_simulation:
        match device_type:
            case DeviceType.MVP_WORKER:
                cmd_args = ["--profile=worker", "--name=test_worker"]
            case DeviceType.DESCALE:
                cmd_args = ["--profile=descale", "--name=test_descale"]
            case DeviceType.POSTMAN:
                cmd_args = ["--profile=postman", "--name=test_postman"]
            case _:
                raise NotImplementedError(f"connection setup not implemented for device {device_type}")
        cmd_args.extend(simulation_args)
        if data_dir:
            cmd_args.append(f"--data-dir={data_dir}")
            
        connection = CLIConnection(device_type.name, None, plugin_config.simulation_exe_path, cmd_args=cmd_args)
    elif modbus_serial_port is not None:
        dev_infos = await create_device_discovery(remote_server_url).list_fw_device_infos(include_unverified_ttys=True)
        dev = next((dev for dev in dev_infos if dev.device_path == modbus_serial_port), None)
        assert dev is not None, "No device detected for the given url"
        connection = ModbusConnection(f"modbus:{modbus_serial_port}", dev, modbus_serial_port, baudrate = 9600, parity = Parity.EVEN)
    else:
        dev_infos = await create_device_discovery(remote_server_url).list_fw_device_infos(include_unverified_ttys=True)
        dev = next((dev for dev in dev_infos if dev.device_path == serial_port), None)
        assert dev is not None, "No device detected for the given url"
        # force remove connection is used for remote devices. 
        # To say remove the previous connection, if ti is still up
        connection = create_connection_to_device(dev, force_remove_connection=True)
    
    return connection


@pytest_asyncio.fixture(scope="package", loop_scope="package", autouse=True)
async def remote_controller(request, tmp_path_factory, create_worker_process):
    # setup
    plugin_config = request.config._sonic_control_plugin
    device_type: DeviceType = plugin_config.device_type
    log_path: Path = plugin_config.log_path

    data_dir: Path = tmp_path_factory.mktemp("data")

    connection = await create_connection(plugin_config, data_dir)
    
    controller = await RemoteController.connect(connection, log_path)
    await controller.stop_updater()
    await controller.stop_running_processes()
    
    assert controller.is_connected, "Controller not connected to device"
    actual_device_type = controller.device_info.device_type 
    assert actual_device_type == device_type, f"Expected to connect to a {device_type} but instead connected to a {actual_device_type}"

    if device_type == DeviceType.POSTMAN:
        # if we have a postman, we want to use it as middleman to the worker
        worker_controller = await controller.connect_to_worker()
        await worker_controller.stop_updater()
        await worker_controller.stop_running_processes()

        yield worker_controller

        await worker_controller.disconnect()

    else:
        yield controller

    # teardown
    await controller.disconnect()


@pytest_asyncio.fixture(scope="function", loop_scope="package", autouse=True)
async def default_remote_test_setup(request, remote_controller):
    if request.node.get_closest_marker("skip_remote_test_setup") is not None:
        yield
        return

    await reset_remote_controller_state(remote_controller)
    yield


def format_command(command_fmt_str: str, *args, consts: DeviceParamConstants | None = None):    
    if args is None:
        return command_fmt_str
    
    if len(args) == 0:
        return command_fmt_str
    
    if consts is None:
        return command_fmt_str.format(*args)

    deduced_args = [resolve_protocol_arg(arg, consts) for arg in args]

    return command_fmt_str.format(*deduced_args)
    

@pytest.fixture(scope="function")
def formatted_command_str(request, remote_controller):
    command_fmt_str, args = request.param
    consts = remote_controller.protocol_consts

    if args is None:
        return command_fmt_str
    
    if not isinstance(args, list):
        args = [ args ]

    return format_command(command_fmt_str, *args, consts=consts)
