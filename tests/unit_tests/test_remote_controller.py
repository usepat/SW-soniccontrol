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

