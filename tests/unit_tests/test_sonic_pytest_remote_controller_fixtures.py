from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from sonic_protocol.command_codes import CommandCode
from sonic_protocol.protocols.protocol_v3_0_0.types.types import Parity
from sonic_protocol.schema import Loglevel

import soniccontrol.fw_device as fw_device
from soniccontrol.fw_device import create_connection_to_device, resolve_current_device_info
from soniccontrol.fw_device.connection import ModbusConnection
from soniccontrol.fw_device.fw_device_info import FwDeviceInfo
from soniccontrol.modbus_defaults import DEFAULT_MODBUS_BAUDRATE, DEFAULT_MODBUS_PARITY, DEFAULT_MODBUS_SLAVE_ID
from soniccontrol_gui.views.configuration.device_settings import ModbusSettings
from sonic_pytest.device_setup import persist_test_log_level
from sonic_pytest.remote_controller import fixtures as remote_fixtures
from sonic_pytest.remote_controller.fixtures import (
    DEFAULT_MODBUS_BAUDRATE as FIXTURE_DEFAULT_MODBUS_BAUDRATE,
    DEFAULT_MODBUS_PARITY as FIXTURE_DEFAULT_MODBUS_PARITY,
    DEFAULT_MODBUS_SLAVE_ID as FIXTURE_DEFAULT_MODBUS_SLAVE_ID,
)
from sonic_pytest.plugin_data import (
    mark_modbus_device_prepared,
    modbus_device_preparation_is_required,
)
from tests.integration_tests.test_modbus import test_modbus as modbus_tests


def test_modbus_connection_defaults_match_shared_defaults():
    connection = ModbusConnection("modbus", None, "/dev/ttyUSB0")

    assert connection.baudrate == DEFAULT_MODBUS_BAUDRATE
    assert connection.parity == DEFAULT_MODBUS_PARITY


def test_create_connection_to_device_uses_shared_modbus_defaults():
    dev_info = FwDeviceInfo(
        sys_name="ttyUSB0",
        subsystem="tty",
        usb_sys_name="1-1",
        device_path="/dev/ttyUSB0",
    )

    connection = create_connection_to_device(dev_info, is_modbus=True)

    assert isinstance(connection, ModbusConnection)
    assert connection.baudrate == DEFAULT_MODBUS_BAUDRATE
    assert connection.parity == DEFAULT_MODBUS_PARITY


def test_gui_modbus_settings_defaults_match_shared_defaults():
    settings = ModbusSettings()

    assert settings.baudrate == DEFAULT_MODBUS_BAUDRATE
    assert settings.parity == DEFAULT_MODBUS_PARITY
    assert settings.server_address == DEFAULT_MODBUS_SLAVE_ID


def test_pytest_fixture_modbus_defaults_match_shared_defaults():
    assert FIXTURE_DEFAULT_MODBUS_BAUDRATE == DEFAULT_MODBUS_BAUDRATE
    assert FIXTURE_DEFAULT_MODBUS_PARITY == DEFAULT_MODBUS_PARITY == Parity.EVEN
    assert FIXTURE_DEFAULT_MODBUS_SLAVE_ID == DEFAULT_MODBUS_SLAVE_ID


@pytest.mark.asyncio
async def test_resolve_current_device_info_falls_back_to_cached_usb_identity(monkeypatch):
    requested_port = "/dev/ttyACM1"
    original = FwDeviceInfo(
        sys_name="ttyACM1",
        subsystem="tty",
        usb_sys_name="1-1",
        device_path=requested_port,
    )
    redetected = FwDeviceInfo(
        sys_name="ttyACM2",
        subsystem="tty",
        usb_sys_name="1-1",
        device_path="/dev/ttyACM2",
    )
    discovery = SimpleNamespace(
        list_fw_device_infos=AsyncMock(side_effect=[[original], [redetected]])
    )

    monkeypatch.setattr(fw_device, "create_device_discovery", lambda *_: discovery)
    fw_device._RESOLVED_DEVICE_INFOS_BY_PATH.clear()

    first = await resolve_current_device_info(requested_port, None)
    second = await resolve_current_device_info(requested_port, None)

    assert first == original
    assert second == redetected
    assert fw_device._RESOLVED_DEVICE_INFOS_BY_PATH[(None, requested_port)] == redetected


@pytest.mark.asyncio
@pytest.mark.parametrize("connection_fails", [False, True])
async def test_modbus_compliance_invalidates_shared_preparation(monkeypatch, connection_fails):
    plugin = SimpleNamespace(
        is_simulation=False,
        modbus_serial_port="/dev/ttyUSB0",
        serial_port="/dev/ttyACM0",
        remote_server_url=None,
        log_path=None,
        _shared_modbus_device_prepared=False,
    )
    node = SimpleNamespace(get_closest_marker=lambda _: None)
    mark_modbus_device_prepared(plugin)
    assert not modbus_device_preparation_is_required(plugin, node)

    controller = SimpleNamespace(
        stop_running_processes=AsyncMock(),
        disconnect=AsyncMock(),
    )
    connect = AsyncMock(return_value=controller)
    if connection_fails:
        connect.side_effect = ConnectionError("Maintenance connection failed")
    monkeypatch.setattr(modbus_tests, "get_sonic_control_plugin", lambda _: plugin)
    monkeypatch.setattr(modbus_tests, "connect_via_serial_port", connect)
    monkeypatch.setattr(
        modbus_tests, "restart_maintenance_controller", AsyncMock(return_value=controller)
    )
    request = SimpleNamespace(config=None)
    fixture = modbus_tests.remote_controller.__wrapped__(request)
    if connection_fails:
        with pytest.raises(ConnectionError, match="Maintenance connection failed"):
            await anext(fixture)
    else:
        assert await anext(fixture) is controller
        await fixture.aclose()
        controller.disconnect.assert_awaited_once()

    assert modbus_device_preparation_is_required(plugin, node)


@pytest.mark.asyncio
async def test_disabled_procedure_skips_reuse_reset_until_test_runs(monkeypatch):
    reset = AsyncMock()
    monkeypatch.setattr(remote_fixtures, "reset_remote_controller_state", reset)
    proc = SimpleNamespace(name="RAMP")
    mark = SimpleNamespace(args=(proc,))

    module = object()

    def node(disabled=False, reprepare=False):
        return SimpleNamespace(
            module=module,
            get_closest_marker=lambda name: True if name == "reprepare_modbus_device" and reprepare else None,
            iter_markers=lambda name: [mark] if disabled and name == "skip_if_proc_not_enabled" else [],
        )

    nodes = [node(disabled=True), node(disabled=True), node(), node(), node(reprepare=True)]
    session = SimpleNamespace(items=nodes)
    controller = SimpleNamespace(is_procedure_enabled=lambda _: False)
    state = remote_fixtures._PreparedTestState()

    for index, item in enumerate(nodes):
        request = SimpleNamespace(node=item, session=session)
        fixture = remote_fixtures.default_remote_test_setup.__wrapped__(request, controller, None, state)
        if index < 2:
            with pytest.raises(pytest.skip.Exception):
                await anext(fixture)
        else:
            assert await anext(fixture) is None
            await fixture.aclose()
        assert reset.await_count == [1, 1, 1, 2, 3][index]


def test_reuse_requires_immediately_preceding_known_clean_skip():
    module = object()
    first = SimpleNamespace(module=module)
    intervening = object()
    node = SimpleNamespace(module=module, get_closest_marker=lambda _: None)
    state = remote_fixtures._PreparedTestState(skipped_item=first)
    request = SimpleNamespace(
        node=node,
        session=SimpleNamespace(items=[first, intervening, node]),
    )
    assert not remote_fixtures._can_reuse_test_state(request, state)


@pytest.mark.asyncio
@pytest.mark.parametrize("reuse", [False, True])
async def test_controller_reconnection_only_reuses_explicitly_clean_setup(monkeypatch, reuse):
    controller = SimpleNamespace(
        stop_updater=AsyncMock(),
        stop_running_processes=AsyncMock(),
        is_connected=True,
        device_info=SimpleNamespace(device_type=remote_fixtures.DeviceType.MVP_WORKER),
    )
    setup = AsyncMock()
    monkeypatch.setattr(remote_fixtures, "create_connection", AsyncMock(return_value=object()))
    monkeypatch.setattr(remote_fixtures.RemoteController, "connect", AsyncMock(return_value=controller))
    monkeypatch.setattr(remote_fixtures, "apply_default_test_setup_over_remote_controller", setup)
    plugin = SimpleNamespace(device_type=remote_fixtures.DeviceType.MVP_WORKER)

    result = await remote_fixtures.build_remote_controller_with_restart(
        plugin, None, None, reuse_test_setup=reuse
    )

    assert result is controller
    assert controller.stop_running_processes.await_count == (0 if reuse else 1)
    assert setup.await_count == (0 if reuse else 1)


@pytest.mark.asyncio
@pytest.mark.parametrize("connected", [False, True])
async def test_procedure_cleanup_uses_maintenance_after_modbus_disconnect(monkeypatch, connected):
    remote = SimpleNamespace(is_connected=lambda: connected)
    maintenance = SimpleNamespace(disconnect=AsyncMock())
    connect = AsyncMock(return_value=maintenance)
    stop = AsyncMock()
    monkeypatch.setattr(procedure_tests, "apply_default_procedure_setup_over_remote_controller", AsyncMock())
    monkeypatch.setattr(procedure_tests, "connect_via_serial_port", connect)
    monkeypatch.setattr(procedure_tests, "send_command_and_check_response", stop)
    plugin = SimpleNamespace(
        modbus_serial_port="/dev/ttyUSB0", serial_port="/dev/ttyACM0",
        remote_server_url=None, log_path=None,
    )
    monkeypatch.setattr(procedure_tests, "get_sonic_control_plugin", lambda _: plugin)
    fixture = procedure_tests.setup_procedures.__wrapped__(SimpleNamespace(config=None), remote)

    await anext(fixture)
    with pytest.raises(StopAsyncIteration):
        await anext(fixture)

    stop.assert_awaited_once()
    assert stop.await_args.args[0] is (remote if connected else maintenance)
    assert connect.await_count == (0 if connected else 1)
    if not connected:
        assert connect.await_args.kwargs["force_remove_connection"] is False
    assert maintenance.disconnect.await_count == (0 if connected else 1)


@pytest.mark.asyncio
async def test_procedure_cleanup_disconnects_maintenance_when_stop_fails(monkeypatch):
    remote = SimpleNamespace(is_connected=lambda: False)
    maintenance = SimpleNamespace(disconnect=AsyncMock())
    plugin = SimpleNamespace(
        modbus_serial_port="/dev/ttyUSB0", serial_port="/dev/ttyACM0",
        remote_server_url=None, log_path=None,
    )
    monkeypatch.setattr(procedure_tests, "apply_default_procedure_setup_over_remote_controller", AsyncMock())
    monkeypatch.setattr(procedure_tests, "connect_via_serial_port", AsyncMock(return_value=maintenance))
    monkeypatch.setattr(
        procedure_tests, "send_command_and_check_response", AsyncMock(side_effect=RuntimeError("stop failed"))
    )
    monkeypatch.setattr(procedure_tests, "get_sonic_control_plugin", lambda _: plugin)
    fixture = procedure_tests.setup_procedures.__wrapped__(SimpleNamespace(config=None), remote)

    await anext(fixture)
    with pytest.raises(RuntimeError, match="stop failed"):
        await anext(fixture)
    maintenance.disconnect.assert_awaited_once()


@pytest.mark.asyncio
async def test_maintenance_connection_can_preserve_existing_remote_connection(monkeypatch):
    device = object()
    connection = object()
    controller = SimpleNamespace(stop_updater=AsyncMock())
    create_connection = Mock(return_value=connection)
    monkeypatch.setattr(remote_fixtures, "resolve_device_info", AsyncMock(return_value=device))
    monkeypatch.setattr(remote_fixtures, "create_connection_to_device", create_connection)
    monkeypatch.setattr(remote_fixtures.RemoteController, "connect", AsyncMock(return_value=controller))
    monkeypatch.setattr(remote_fixtures, "_has_valid_deduced_protocol", lambda _: True)

    assert await remote_fixtures.connect_via_serial_port(
        "/dev/ttyACM0", None, None, force_remove_connection=False
    ) is controller
    create_connection.assert_called_once_with(device, force_remove_connection=False)