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