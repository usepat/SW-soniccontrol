import contextlib
import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import List
import pytest
import pytest_asyncio
from sonic_protocol.protocols.protocol_v3_0_0.types.types import Parity
from sonic_protocol.field_names import EFieldName
from sonic_protocol.schema import ControlMode, DeviceParamConstants, Loglevel, Version
from soniccontrol import DeviceParamConstantType
from soniccontrol import commands as cmds
from sonic_protocol.python_parser import commands
from soniccontrol.data_capturing.device_performance.performance_monitor import PerformanceMonitor
from soniccontrol.fw_device.connection import CLIConnection, ModbusConnection
from soniccontrol.fw_device import create_connection_to_device, create_device_discovery, resolve_current_device_info
from soniccontrol.modbus_defaults import DEFAULT_MODBUS_BAUDRATE, DEFAULT_MODBUS_PARITY, DEFAULT_MODBUS_SLAVE_ID
from soniccontrol import RemoteController, DeviceType
from sonic_pytest.remote_controller.asserts import send_command_and_check_response
from sonic_pytest.plugin_data import SonicControlPlugin, mark_modbus_device_prepared, modbus_device_preparation_is_required
from sonic_pytest.fixtures import create_worker_process_impl


create_worker_process = pytest_asyncio.fixture(create_worker_process_impl, scope="package", loop_scope="package")

async def reset_remote_controller_state(remote_controller: RemoteController) -> None:
    if not remote_controller._device._uses_modbus():
        await send_command_and_check_response(remote_controller, commands.SetLogLevel("global", Loglevel.ERROR))

    await send_command_and_check_response(remote_controller, commands.SetControlMode(ControlMode.REMOTE))
    await send_command_and_check_response(remote_controller, commands.ClearErrors())
    await send_command_and_check_response(remote_controller, commands.SonicForce())
    await send_command_and_check_response(remote_controller, commands.SetStop(), raise_exception = False)
    await send_command_and_check_response(remote_controller, commands.SetOff())


def resolve_protocol_arg(arg, consts: DeviceParamConstants | None = None):
    if consts is None:
        return arg
    if isinstance(arg, DeviceParamConstantType):
        return getattr(consts, arg.value)
    return arg


async def resolve_device_info(serial_port: str, remote_server_url: str | None):
    return await resolve_current_device_info(serial_port, remote_server_url)


def _has_valid_deduced_protocol(controller: RemoteController) -> bool:
    device_info = controller.device_info
    return (
        device_info.device_type != DeviceType.UNKNOWN
        and device_info.protocol_version != Version(0, 0, 0)
    )


async def connect_via_serial_port(
    serial_port: str,
    remote_server_url: str | None,
    log_path: Path,
    timeout_s: float = 10.0,
    retry_interval_s: float = 0.25,
) -> RemoteController:
    deadline = asyncio.get_running_loop().time() + timeout_s
    last_error: Exception | None = None

    while True:
        controller: RemoteController | None = None
        try:
            dev = await resolve_device_info(serial_port, remote_server_url)
            connection = create_connection_to_device(dev, force_remove_connection=True)
            controller = await RemoteController.connect(connection, log_path)
            await controller.stop_updater()

            if not _has_valid_deduced_protocol(controller):
                raise RuntimeError(
                    f"Connected to {serial_port}, but protocol deduction returned "
                    f"{controller.device_info.device_type.value}/{controller.device_info.protocol_version}"
                )

            return controller
        except Exception as exc:
            last_error = exc
            if controller is not None:
                with contextlib.suppress(Exception):
                    await controller.disconnect()
            if asyncio.get_running_loop().time() >= deadline:
                raise RuntimeError(
                    f"Timed out connecting to serial port {serial_port} after restart"
                ) from last_error
            await asyncio.sleep(retry_interval_s)


async def restart_and_wait_for_maintenance_redetection(
    controller: RemoteController,
    log_path: Path,
    restart_command: commands.Command = commands.RestartDevice(),
    timeout_s: float = 10.0,
) -> None:
    connection = controller.device.communicator.connection
    assert connection is not None, "Controller has no active connection"
    previous_dev_info = connection.dev_info
    assert previous_dev_info is not None, "Controller connection has no device info"

    # RemoteController.restart() already performs its own redetection and rebuild.
    # This helper owns the reconnect flow explicitly, so only issue the raw device restart here.
    await controller.device.restart(restart_command)

    device_discovery = create_device_discovery(previous_dev_info.remote_server_url)
    await device_discovery.wait_for_device_redetection(previous_dev_info, timeout_s=timeout_s)

    # Redetection only proves the maintenance USB device re-enumerated.
    # Reconnect once over the maintenance channel to prove the protocol is responsive again
    # before any modbus-side reconnect depends on it.
    maintenance_probe = await connect_via_serial_port(
        previous_dev_info.device_path,
        previous_dev_info.remote_server_url,
        log_path,
        timeout_s=timeout_s,
    )
    await maintenance_probe.disconnect()


async def apply_modbus_user_settings(
    controller: RemoteController,
    baudrate: int = DEFAULT_MODBUS_BAUDRATE,
    parity: Parity = DEFAULT_MODBUS_PARITY,
    slave_id: int = DEFAULT_MODBUS_SLAVE_ID,
) -> None:
    await controller.send_command(commands.SetModbusParity(parity), raise_exception=True)
    await controller.send_command(commands.SetModbusBaudrate(baudrate), raise_exception=True)
    await controller.send_command(commands.SetModbusServerAddress(slave_id), raise_exception=True)

    answer = await controller.send_command(commands.GetModbusSettings(), raise_exception=True)
    assert answer.valid, f"GetModbusSettings returned an invalid answer: {answer.message}"
    assert answer[EFieldName.PARITY] == parity, (
        f"Expected modbus parity {parity}, got {answer[EFieldName.PARITY]}"
    )
    assert answer[EFieldName.BAUDRATE] == baudrate, (
        f"Expected modbus baudrate {baudrate}, got {answer[EFieldName.BAUDRATE]}"
    )
    assert answer[EFieldName.MODBUS_SERVER_ID] == slave_id, (
        f"Expected modbus slave id {slave_id}, got {answer[EFieldName.MODBUS_SERVER_ID]}"
    )


async def restart_maintenance_controller(
    controller: RemoteController,
    serial_port: str,
    remote_server_url: str | None,
    log_path: Path,
    restart_command: commands.Command,
) -> RemoteController:
    await restart_and_wait_for_maintenance_redetection(
        controller,
        log_path,
        restart_command=restart_command,
    )
    with contextlib.suppress(Exception):
        await controller.disconnect()
    return await connect_via_serial_port(serial_port, remote_server_url, log_path)


async def ensure_modbus_settings_controller(
    controller: RemoteController,
    serial_port: str,
    remote_server_url: str | None,
    log_path: Path,
) -> RemoteController:
    if controller.device.has_command(commands.GetModbusSettings()):
        return controller

    if not controller.device.has_command(commands.StartCustomizer()):
        controller = await restart_maintenance_controller(
            controller,
            serial_port,
            remote_server_url,
            log_path,
            commands.StartOperator(),
        )

    return await restart_maintenance_controller(
        controller,
        serial_port,
        remote_server_url,
        log_path,
        commands.StartCustomizer(),
    )


async def prepare_modbus_device(plugin_config: SonicControlPlugin, log_path: Path) -> None:
    serial_port: str | None = plugin_config.serial_port
    assert serial_port is not None, "A maintenance serial port is required for modbus-enabled tests"

    maintenance_controller = await connect_via_serial_port(serial_port, plugin_config.remote_server_url, log_path)
    try:
        await maintenance_controller.stop_running_processes()
        maintenance_controller = await ensure_modbus_settings_controller(
            maintenance_controller,
            serial_port,
            plugin_config.remote_server_url,
            log_path,
        )
        await apply_modbus_user_settings(maintenance_controller)
        await restart_and_wait_for_maintenance_redetection(
            maintenance_controller,
            log_path,
        )
    finally:
        with contextlib.suppress(Exception):
            await maintenance_controller.disconnect()


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
        dev = await resolve_device_info(modbus_serial_port, remote_server_url)
        connection = ModbusConnection(
            f"modbus:{modbus_serial_port}",
            dev,
            modbus_serial_port,
            baudrate=DEFAULT_MODBUS_BAUDRATE,
            parity=DEFAULT_MODBUS_PARITY,
        )
    else:
        assert serial_port is not None, "No device port was configured"
        dev = await resolve_device_info(serial_port, remote_server_url)
        # force remove connection is used for remote devices.
        # To say remove the previous connection, if it is still up.
        connection = create_connection_to_device(dev, force_remove_connection=True)
    
    return connection


async def build_remote_controller(plugin_config: SonicControlPlugin, data_dir: Path, log_path: Path) -> RemoteController:
    return await build_remote_controller_with_restart(plugin_config, data_dir, log_path)


async def build_remote_controller_with_restart(
    plugin_config: SonicControlPlugin,
    data_dir: Path,
    log_path: Path,
    restart_executor: Callable[[commands.Command, RemoteController], Awaitable[RemoteController]] | None = None,
) -> RemoteController:
    connection = await create_connection(plugin_config, data_dir, ["--board-type=simulation"])
    controller = await RemoteController.connect(connection, log_path, restart_executor=restart_executor)
    await controller.stop_updater()
    await controller.stop_running_processes()

    device_type: DeviceType = plugin_config.device_type
    assert controller.is_connected, "Controller not connected to device"
    actual_device_type = controller.device_info.device_type
    assert actual_device_type == device_type, f"Expected to connect to a {device_type} but instead connected to a {actual_device_type}"

    if device_type == DeviceType.POSTMAN:
        worker_controller = await controller.connect_to_worker()
        await worker_controller.stop_updater()
        await worker_controller.stop_running_processes()
        return worker_controller

    return controller


@pytest_asyncio.fixture(scope="package", loop_scope="package")
async def package_remote_controller(request, tmp_path_factory, create_worker_process):
    # setup
    plugin_config = request.config._sonic_control_plugin
    log_path: Path = plugin_config.log_path

    if not plugin_config.is_simulation and plugin_config.modbus_serial_port is not None:
        yield None
        return

    data_dir: Path = tmp_path_factory.mktemp("data")
    controller = await build_remote_controller(plugin_config, data_dir, log_path)

    yield controller

    with contextlib.suppress(Exception):
        await controller.disconnect()


@pytest_asyncio.fixture(scope="function", loop_scope="package", autouse=True)
async def remote_controller(request, tmp_path_factory, create_worker_process, package_remote_controller):
    plugin_config = request.config._sonic_control_plugin
    log_path: Path = plugin_config.log_path

    if plugin_config.is_simulation or plugin_config.modbus_serial_port is None:
        assert package_remote_controller is not None
        yield package_remote_controller
        return

    data_dir: Path = tmp_path_factory.mktemp("data")
    if modbus_device_preparation_is_required(plugin_config, request.node):
        await prepare_modbus_device(plugin_config, log_path)
        mark_modbus_device_prepared(plugin_config)

    async def restart_via_maintenance_channel(
        restart_command: commands.Command,
        _: RemoteController,
    ) -> RemoteController:
        serial_port = plugin_config.serial_port
        assert serial_port is not None, "A maintenance serial port is required for restart handling"

        maintenance_controller = await connect_via_serial_port(
            serial_port,
            plugin_config.remote_server_url,
            log_path,
        )
        try:
            await restart_and_wait_for_maintenance_redetection(
                maintenance_controller,
                log_path,
                restart_command=restart_command,
            )
        finally:
            with contextlib.suppress(Exception):
                await maintenance_controller.disconnect()

        return await build_remote_controller_with_restart(
            plugin_config,
            data_dir,
            log_path,
            restart_executor=restart_via_maintenance_channel,
        )

    controller = await build_remote_controller_with_restart(
        plugin_config,
        data_dir,
        log_path,
        restart_executor=restart_via_maintenance_channel,
    )
    try:
        yield controller
    finally:
        with contextlib.suppress(Exception):
            await controller.disconnect()


@pytest_asyncio.fixture(scope="function", loop_scope="package", autouse=True)
async def performance_monitor(remote_controller):
    device = remote_controller.device
    monitor = PerformanceMonitor(device)

    yield monitor

    was_updater_running = remote_controller._updater.running.is_set()
    if was_updater_running:
        await remote_controller.stop_updater()

    if device.communicator.connection_opened.is_set() and device.has_command(cmds.GetNumAllocators()):
        snap_shot = await monitor.sample_memory_snapshot()
        snap_shot.check_performance()

    if was_updater_running and remote_controller.is_connected():
        remote_controller.start_updater()


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
