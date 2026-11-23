from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sonic_protocol.protocols.protocol_v3_0_0.types.types import Parity

import soniccontrol.fw_device as fw_device
from soniccontrol.fw_device import create_connection_to_device, resolve_current_device_info
from soniccontrol.fw_device.connection import ModbusConnection
from soniccontrol.fw_device.fw_device_info import FwDeviceInfo
from soniccontrol.modbus_defaults import DEFAULT_MODBUS_BAUDRATE, DEFAULT_MODBUS_PARITY, DEFAULT_MODBUS_SLAVE_ID
from soniccontrol_gui.views.configuration.device_settings import ModbusSettings
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