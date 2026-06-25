import logging
from unittest.mock import AsyncMock, Mock

import pytest

from sonic_protocol.python_parser import commands
from soniccontrol.fw_device.fw_device_info import FwDeviceInfo
import soniccontrol.remote_controller as remote_controller_module
from soniccontrol.remote_controller import RemoteController


@pytest.mark.asyncio
async def test_restart_uses_custom_restart_executor():
    logger = logging.getLogger("test")
    original_device = Mock()
    original_device._logger = logger
    original_device.restart = AsyncMock()
    original_device.communicator.connection = object()

    replacement_device = Mock()
    replacement_device._logger = logger
    replacement_device.communicator = Mock()

    replacement_controller = RemoteController(replacement_device, logger)
    replacement_controller.stop_updater = AsyncMock()
    replacement_controller.start_updater = Mock()

    restart_executor = AsyncMock(return_value=replacement_controller)

    controller = RemoteController(original_device, logger, restart_executor=restart_executor)
    controller._updater.stop = AsyncMock()
    controller._updater.running.is_set = Mock(return_value=False)

    await controller.restart(commands.StartCustomizer())

    restart_executor.assert_awaited_once_with(commands.StartCustomizer(), controller)
    original_device.restart.assert_not_awaited()
    replacement_controller.stop_updater.assert_awaited_once()
    assert controller.device is replacement_device


@pytest.mark.asyncio
async def test_restart_preserves_running_updater_on_replacement():
    logger = logging.getLogger("test")
    original_device = Mock()
    original_device._logger = logger
    original_device.restart = AsyncMock()
    original_device.communicator.connection = object()

    replacement_device = Mock()
    replacement_device._logger = logger
    replacement_device.communicator = Mock()

    replacement_controller = RemoteController(replacement_device, logger)
    replacement_controller.stop_updater = AsyncMock()
    replacement_controller.start_updater = Mock()

    restart_executor = AsyncMock(return_value=replacement_controller)

    controller = RemoteController(original_device, logger, restart_executor=restart_executor)
    controller._updater.stop = AsyncMock()
    controller._updater.running.is_set = Mock(return_value=True)

    await controller.restart()

    replacement_controller.start_updater.assert_called_once_with()
    replacement_controller.stop_updater.assert_not_awaited()
    assert controller.device is replacement_device


@pytest.mark.asyncio
async def test_connect_via_serial_uses_shared_device_resolution(monkeypatch):
    resolved_dev_info = FwDeviceInfo(
        sys_name="ttyACM2",
        subsystem="tty",
        usb_sys_name="1-1",
        device_path="/dev/ttyACM2",
    )
    resolved_connection = object()
    expected_controller = object()

    resolve_current_device_info = AsyncMock(return_value=resolved_dev_info)
    create_connection_to_device = Mock(return_value=resolved_connection)
    connect = AsyncMock(return_value=expected_controller)

    monkeypatch.setattr(remote_controller_module, "resolve_current_device_info", resolve_current_device_info)
    monkeypatch.setattr(remote_controller_module, "create_connection_to_device", create_connection_to_device)
    monkeypatch.setattr(remote_controller_module.RemoteController, "connect", connect)

    controller = await RemoteController.connect_via_serial("/dev/ttyACM1")

    resolve_current_device_info.assert_awaited_once_with("/dev/ttyACM1")
    create_connection_to_device.assert_called_once_with(resolved_dev_info, 9600)
    connect.assert_awaited_once_with(resolved_connection, None)
    assert controller is expected_controller