import contextlib
from typing import NamedTuple
import asyncio
import logging

import pytest
import pytest_asyncio
from pymodbus.client import AsyncModbusSerialClient
from pymodbus.exceptions import ModbusIOException
from sonic_protocol.schema import DeviceType
from soniccontrol import RemoteController, commands, Parity
from sonic_pytest.remote_controller.fixtures import (
    apply_modbus_user_settings,
    connect_via_serial_port,
    ensure_modbus_settings_controller,
    reset_remote_controller_state,
    restart_maintenance_controller,
)

"""
I think it makes only sense to test a single read and write multiple registers here.
Because all modbus tests that could be implemented are better to implement directly 
as unit tests for the application_server and application_client classes in the firmware.
The only thing really needed to test would be timing, crc, issues, slave addressing, but
that can also be tested in the firmware with a loopback.

So this here is just a simple test for compliance. To check if it works at all with an 
extern implementation of modbus with different serial settings.

Note: this file cannot be part of test_remote folder as there a remote_controller is used via auto-use.
Therefore to avoid issues, it is better to isolate this here
"""


class ModbusClientContext(NamedTuple):
    client: AsyncModbusSerialClient
    slave_id: int
    port: str
    baudrate: int
    parity: str
    stopbits: int
    maintenance_controller: RemoteController


async def close_modbus_client(client: AsyncModbusSerialClient, settle_time_s: float = 0.25) -> None:
    client.close()
    await asyncio.sleep(settle_time_s)


async def create_modbus_client(
    port: str,
    baudrate: int,
    parity: str,
    stopbits: int,
    timeout_s: float = 10.0,
    retry_interval_s: float = 0.25,
) -> AsyncModbusSerialClient:
    deadline = asyncio.get_running_loop().time() + timeout_s
    last_error: Exception | None = None

    while True:
        client = AsyncModbusSerialClient(
            port,
            baudrate=baudrate,
            parity=parity,
            stopbits=stopbits,
            timeout=1.5,
            retries=3,
        )
        try:
            connected = await client.connect()
            if connected:
                return client

            last_error = ConnectionError(f"Modbus client could not connect to {port}")
        except Exception as exc:
            last_error = exc

        await close_modbus_client(client)
        if asyncio.get_running_loop().time() >= deadline:
            raise RuntimeError(
                f"Timed out connecting modbus client to {port} after restart"
            ) from last_error
        await asyncio.sleep(retry_interval_s)


def parity_to_client_value(parity: Parity) -> str:
    if parity == Parity.EVEN:
        return "E"
    if parity == Parity.ODD:
        return "O"
    return "N"


def get_invalid_slave_id(slave_id: int) -> int:
    return slave_id + 1 if slave_id < 247 else slave_id - 1


async def assert_modbus_settings_respond(
    port: str,
    baudrate: int,
    parity: str,
    slave_id: int,
) -> None:
    stopbits = 1 if parity != "N" else 2
    client = await create_modbus_client(port, baudrate, parity, stopbits)
    try:
        answer = await client.read_input_registers(1024, count=1, device_id=slave_id)
        assert not answer.isError(), "Expected configured modbus settings to respond"

        with pytest.raises(ModbusIOException, match="No response received"):
            await client.read_input_registers(
                1024,
                count=1,
                device_id=get_invalid_slave_id(slave_id),
            )
    finally:
        await close_modbus_client(client)


async def assert_modbus_client_responds(modbus_client: ModbusClientContext) -> None:
    answer = await modbus_client.client.read_input_registers(1024, count=1, device_id=modbus_client.slave_id)
    assert not answer.isError(), "Expected configured modbus settings to respond"

    with pytest.raises(ModbusIOException, match="No response received"):
        await modbus_client.client.read_input_registers(
            1024,
            count=1,
            device_id=get_invalid_slave_id(modbus_client.slave_id),
        )


@pytest_asyncio.fixture(scope="function", loop_scope="package")
async def remote_controller(request):
    plugin = request.config._sonic_control_plugin
    serial_port: str | None = plugin.serial_port
    modbus_serial_port: str | None = plugin.modbus_serial_port
    if plugin.is_simulation:
        pytest.skip("These modbus test do not work for the simulation right now")
    if serial_port is None or modbus_serial_port is None:
        pytest.skip("Both maintenance and modbus serial ports are required for modbus compliance tests")
    if serial_port == modbus_serial_port:
        pytest.skip("Maintenance and modbus serial ports need to be different")
    maintenance_controller = await connect_via_serial_port(serial_port, plugin.remote_server_url, plugin.log_path)
    try:
        await maintenance_controller.stop_running_processes()
        maintenance_controller = await restart_maintenance_controller(
            maintenance_controller,
            serial_port,
            plugin.remote_server_url,
            plugin.log_path,
            commands.StartOperator(),
        )
        yield maintenance_controller
    finally:
        await maintenance_controller.disconnect()


@pytest_asyncio.fixture(scope="function", loop_scope="package", autouse=True)
async def default_remote_test_setup(request):
    yield

    plugin = request.config._sonic_control_plugin
    serial_port: str | None = plugin.serial_port
    if plugin.is_simulation or serial_port is None:
        return

    restore_logger = logging.getLogger(__name__)
    maintenance_controller: RemoteController | None = None
    try:
        maintenance_controller = await connect_via_serial_port(
            serial_port,
            plugin.remote_server_url,
            plugin.log_path,
        )
        await maintenance_controller.stop_running_processes()
        maintenance_controller = await restart_maintenance_controller(
            maintenance_controller,
            serial_port,
            plugin.remote_server_url,
            plugin.log_path,
            commands.StartOperator(),
        )
        await reset_remote_controller_state(maintenance_controller)
    except Exception as exc:
        restore_logger.warning("Failed to restore modbus test device state after test: %s", exc)
    finally:
        if maintenance_controller is not None:
            with contextlib.suppress(Exception):
                await maintenance_controller.disconnect()

@pytest_asyncio.fixture(scope="function", loop_scope="package", params=[
    (9600, "E", 1),
    (9600, "O", 1),
    (9600, "N", 1),
    (19200, "E", 1),
    (19200, "O", 1),
    (19200, "N", 1),
    (19200, "E", 2),
    (19200, "E", 5),
    (19200, "E", 19),
])
async def modbus_client(request, remote_controller):
    baudrate, parity, slave_id = request.param
    plugin = request.config._sonic_control_plugin
    serial_port: str | None = plugin.serial_port
    port: str | None = plugin.modbus_serial_port

    if serial_port is None:
        pytest.skip("No maintenance serial port was set. Skip modbus compliance tests")
    
    if parity == "E":
        prot_parity = Parity.EVEN
    elif parity == "O":
        prot_parity = Parity.ODD
    else:
        prot_parity = Parity.NO
    maintenance_controller = await ensure_modbus_settings_controller(
        remote_controller,
        serial_port,
        plugin.remote_server_url,
        plugin.log_path,
    )
    try:
        await apply_modbus_user_settings(maintenance_controller, baudrate, prot_parity, slave_id)
        maintenance_controller = await restart_maintenance_controller(
            maintenance_controller,
            serial_port,
            plugin.remote_server_url,
            plugin.log_path,
            commands.RestartDevice(),
        )

        if port is None:
            pytest.skip("No modbus serial port was set. Skip modbus compliance tests")

        stopbits = 1 if prot_parity != Parity.NO else 2
        client = await create_modbus_client(port, baudrate, parity, stopbits)
        try:
            yield ModbusClientContext(client, slave_id, port, baudrate, parity, stopbits, maintenance_controller)
        finally:
            await close_modbus_client(client)
    finally:
        await maintenance_controller.disconnect()


@pytest_asyncio.fixture(scope="function", loop_scope="package", params=[
    (19200, "E", 1),
    (9600, "N", 5),
    (19200, "O", 19),
])
async def modbus_persistence_client(request, remote_controller):
    baudrate, parity, slave_id = request.param
    plugin = request.config._sonic_control_plugin
    serial_port: str | None = plugin.serial_port
    port: str | None = plugin.modbus_serial_port

    if serial_port is None:
        pytest.skip("No maintenance serial port was set. Skip modbus compliance tests")

    if parity == "E":
        prot_parity = Parity.EVEN
    elif parity == "O":
        prot_parity = Parity.ODD
    else:
        prot_parity = Parity.NO

    maintenance_controller = await ensure_modbus_settings_controller(
        remote_controller,
        serial_port,
        plugin.remote_server_url,
        plugin.log_path,
    )
    try:
        await apply_modbus_user_settings(maintenance_controller, baudrate, prot_parity, slave_id)
        maintenance_controller = await restart_maintenance_controller(
            maintenance_controller,
            serial_port,
            plugin.remote_server_url,
            plugin.log_path,
            commands.RestartDevice(),
        )

        if port is None:
            pytest.skip("No modbus serial port was set. Skip modbus compliance tests")

        stopbits = 1 if prot_parity != Parity.NO else 2
        client = await create_modbus_client(port, baudrate, parity, stopbits)
        try:
            yield ModbusClientContext(client, slave_id, port, baudrate, parity, stopbits, maintenance_controller)
        finally:
            await close_modbus_client(client)
    finally:
        await maintenance_controller.disconnect()

@pytest.mark.allowed_devices(DeviceType.POSTMAN, DeviceType.MVP_WORKER, DeviceType.DESCALE)
@pytest.mark.asyncio(loop_scope="package")
async def test_modbus_write_and_read_multiple_registers(modbus_client: AsyncModbusSerialClient):
    # note. first register should be 0, 
    # because that address corresponds to the execute_command_flag, 
    # that we do not want to set
    client, slave_id, *_ = modbus_client
    data = [0, 1, 2, 3, 0]
    answer = await client.write_registers(1024, data, device_id=slave_id)
    assert not answer.isError(), "modbus write failed"
    answer = await client.read_input_registers(1024, count=len(data), device_id=slave_id)
    assert not answer.isError(), "modbus read failed"

    assert answer.registers == data, "The data read does not correspond to the data written"


@pytest.mark.allowed_devices(DeviceType.POSTMAN, DeviceType.MVP_WORKER, DeviceType.DESCALE)
@pytest.mark.asyncio(loop_scope="package")
async def test_modbus_invalid_slave_id_gets_no_response(modbus_client: ModbusClientContext):
    invalid_slave_id = get_invalid_slave_id(modbus_client.slave_id)

    with pytest.raises(ModbusIOException, match="No response received"):
        await modbus_client.client.read_input_registers(1024, count=1, device_id=invalid_slave_id)



@pytest.mark.allowed_devices(DeviceType.POSTMAN, DeviceType.MVP_WORKER, DeviceType.DESCALE)
@pytest.mark.asyncio(loop_scope="package")
async def test_modbus_slave_id_persists_after_second_restart(
    modbus_client: ModbusClientContext,
):
    await assert_modbus_client_responds(modbus_client)
    await modbus_client.maintenance_controller.restart()
    await modbus_client.maintenance_controller.restart()

    await assert_modbus_client_responds(modbus_client)
        


@pytest.mark.allowed_devices(DeviceType.POSTMAN, DeviceType.MVP_WORKER, DeviceType.DESCALE)
@pytest.mark.asyncio(loop_scope="package")
@pytest.mark.parametrize(
    "first_restart_command",
    [
        pytest.param(commands.RestartDevice(), id="restart-then-restart"),
        pytest.param(commands.StartOperator(), id="start-operator-then-restart"),
        pytest.param(commands.StartCustomizer(), id="start-customizer-then-restart"),
        pytest.param(commands.StartDiagnosticsTool(), id="start-diagnostics-then-restart"),
    ],
)
async def test_default_modbus_settings_preserved_across_noninteractive_restart_sequence(
    modbus_persistence_client: ModbusClientContext,
    first_restart_command,
):
    await assert_modbus_client_responds(modbus_persistence_client)

    await modbus_persistence_client.maintenance_controller.restart(first_restart_command)
    await modbus_persistence_client.maintenance_controller.restart()

    await assert_modbus_client_responds(modbus_persistence_client)
