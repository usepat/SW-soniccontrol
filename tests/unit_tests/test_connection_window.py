from unittest.mock import AsyncMock, Mock

import pytest

from sonic_protocol.python_parser.answer import Answer
import soniccontrol_gui.views.core.connection_window as connection_window_module
from soniccontrol.communication.modbus_communicator import ModbusCommunicator
from soniccontrol.sonic_device import SonicDevice
from soniccontrol_gui.views.core.connection_window import DeviceWindowManager


@pytest.mark.asyncio
async def test_wait_for_modbus_ready_retries_until_probe_succeeds(monkeypatch):
    manager = DeviceWindowManager(None)
    sleep_mock = AsyncMock()
    monkeypatch.setattr(connection_window_module.asyncio, "sleep", sleep_mock)

    device = Mock(spec=SonicDevice)
    device.communicator = ModbusCommunicator()
    device.execute_command = AsyncMock(
        side_effect=[
            Answer("not ready", False, True),
            Answer("ok", True, True),
        ]
    )

    await manager._wait_for_modbus_ready(device)

    assert device.execute_command.await_count == 2
    assert device.execute_command.await_args_list[0].args[0].code == connection_window_module.commands.GetProtocol().code
    assert device.execute_command.await_args_list[1].args[0].code == connection_window_module.commands.GetProtocol().code
    for await_call in device.execute_command.await_args_list:
        assert await_call.kwargs["raise_exception"] is False
        assert await_call.kwargs["disconnect_on_exception"] is False
        assert await_call.kwargs["should_log"] is False
    sleep_mock.assert_awaited_once_with(manager.MODBUS_READY_PROBE_DELAY_S)