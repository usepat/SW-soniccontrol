from pathlib import Path
import pytest
import pytest_asyncio
from sonic_protocol.schema import DeviceParamConstants
from soniccontrol import DeviceParamConstantType
from soniccontrol.fw_device.connection import CLIConnection
from soniccontrol.fw_device import create_connection_to_device, create_device_discovery
from soniccontrol import RemoteController, DeviceType
from tests.integration_tests.conftest import create_worker_process_impl


create_worker_process = pytest_asyncio.fixture(create_worker_process_impl, scope="package", loop_scope="package")


async def reset_remote_controller_state(remote_controller: RemoteController) -> None:
    await remote_controller.send_command("!log[global]=ERROR")
    await remote_controller.send_command("!control=remote")
    await remote_controller.send_command("!clear_errors")
    await remote_controller.send_command("!sonic_force")
    await remote_controller.send_command("!stop")
    await remote_controller.send_command("!OFF")


@pytest_asyncio.fixture(scope="package", loop_scope="package", autouse=True)
async def remote_controller(request, tmp_path_factory, create_worker_process):
    # setup
    plugin_config = request.config._sonic_control_plugin
    is_simulation: bool = plugin_config.is_simulation
    device_type: DeviceType = plugin_config.device_type
    url: str = plugin_config.serial_port
    log_path: Path = plugin_config.log_path
    remote_server_url: str | None = plugin_config.remote_server_url

    data_dir: Path = tmp_path_factory.mktemp("data")
    data_dir_arg = f"--data-dir={data_dir}"

    connection = None
    if is_simulation:
        match device_type:
            case DeviceType.MVP_WORKER:
                cmd_args = ["--profile=worker", "--name=test_worker", data_dir_arg]
            case DeviceType.DESCALE:
                cmd_args = ["--profile=descale", "--name=test_descale", data_dir_arg]
            case DeviceType.POSTMAN:
                cmd_args = ["--profile=postman", "--name=test_postman", data_dir_arg]
            case _:
                raise NotImplementedError(f"connection setup not implemented for device {device_type}")
        connection = CLIConnection(device_type.name, None, plugin_config.simulation_exe_path, cmd_args=cmd_args)
    else:
        dev_infos = await create_device_discovery(remote_server_url).list_fw_device_infos()
        dev = next((dev for dev in dev_infos if dev.device_path == url), None)
        assert dev is not None, "No device detected for the given url"
        # force remove connection is used for remote devices. 
        # To say remove the previous connection, if ti is still up
        connection = create_connection_to_device(dev, force_remove_connection=True)

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

    deduced_args = []
    for arg in args:
        deduced_arg = getattr(consts, arg.value) if isinstance(arg, DeviceParamConstantType) else arg
        deduced_args.append(deduced_arg)

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
