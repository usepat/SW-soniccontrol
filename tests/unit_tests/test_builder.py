import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, call

import pytest

import sonic_protocol.python_parser.commands as cmds
import soniccontrol.builder as builder_module
from sonic_protocol.python_parser.answer import Answer, ValidationStatus
from sonic_protocol.schema import DeviceType
from soniccontrol.builder import DeviceBuilder


def _communicator_mock() -> Mock:
    communicator = Mock()
    communicator.open_communication = AsyncMock()
    return communicator


def _device_mock(device_type: DeviceType, supports_start_configurator: bool = False) -> Mock:
    device = Mock()
    device.info = SimpleNamespace(device_type=device_type)
    device.has_command.return_value = supports_start_configurator
    device.execute_command = AsyncMock(return_value=Answer("ok", ValidationStatus.VALID))
    device.disconnect = AsyncMock()
    device.restart = AsyncMock()
    return device


@pytest.mark.asyncio
async def test_build_configurator_returns_existing_configurator(monkeypatch):
    builder = DeviceBuilder(logger=logging.getLogger("test_builder"))
    communicator = _communicator_mock()
    serial_communicator_factory = Mock(return_value=communicator)
    monkeypatch.setattr(builder_module, "SerialCommunicator", serial_communicator_factory)

    configurator = _device_mock(DeviceType.CONFIGURATOR)
    builder.build_amp = AsyncMock(return_value=configurator)  # type: ignore[method-assign]

    connection = Mock()
    result = await builder.build_configurator(connection)

    assert result is configurator
    communicator.open_communication.assert_awaited_once_with(connection)
    builder.build_amp.assert_awaited_once_with(communicator, try_deduce_protocol_used=True)
    configurator.execute_command.assert_not_called()
    configurator.disconnect.assert_not_called()


@pytest.mark.asyncio
async def test_build_configurator_switches_mode_and_rebuilds(monkeypatch):
    builder = DeviceBuilder(logger=logging.getLogger("test_builder"))
    first_communicator = _communicator_mock()
    second_communicator = _communicator_mock()
    serial_communicator_factory = Mock(side_effect=[first_communicator, second_communicator])
    monkeypatch.setattr(builder_module, "SerialCommunicator", serial_communicator_factory)

    amp = _device_mock(DeviceType.DESCALE, supports_start_configurator=True)
    configurator = _device_mock(DeviceType.CONFIGURATOR)
    builder.build_amp = AsyncMock(side_effect=[amp, configurator])  # type: ignore[method-assign]

    connection = Mock()
    new_connection = Mock()
    redetect_connection_mock = AsyncMock(return_value=new_connection)
    monkeypatch.setattr(builder_module, "redetect_connection", redetect_connection_mock)
    result = await builder.build_configurator(connection, try_deduce_protocol_used=False)

    assert result is configurator
    assert serial_communicator_factory.call_count == 2
    first_communicator.open_communication.assert_awaited_once_with(connection)
    redetect_connection_mock.assert_awaited_once_with(connection)
    second_communicator.open_communication.assert_awaited_once_with(new_connection)
    assert builder.build_amp.await_args_list == [
        call(first_communicator, try_deduce_protocol_used=False),
        call(second_communicator, try_deduce_protocol_used=False),
    ]

    amp.restart.assert_awaited_once()
    command = amp.restart.await_args.args[0]
    assert isinstance(command, cmds.StartConfigurator)
    assert command.value == "secure_password"
    amp.execute_command.assert_not_called()
    amp.disconnect.assert_not_called()


@pytest.mark.asyncio
async def test_build_configurator_re_raises_restart_failure(monkeypatch):
    builder = DeviceBuilder(logger=logging.getLogger("test_builder"))
    communicator = _communicator_mock()
    serial_communicator_factory = Mock(return_value=communicator)
    monkeypatch.setattr(builder_module, "SerialCommunicator", serial_communicator_factory)

    amp = _device_mock(DeviceType.DESCALE, supports_start_configurator=True)
    amp.restart = AsyncMock(side_effect=ConnectionError("device disconnected"))
    builder.build_amp = AsyncMock(return_value=amp)  # type: ignore[method-assign]

    with pytest.raises(ConnectionError, match="device disconnected"):
        await builder.build_configurator(Mock())

    amp.execute_command.assert_not_called()
    amp.disconnect.assert_not_called()


@pytest.mark.asyncio
async def test_build_configurator_re_raises_unexpected_restart_failure(monkeypatch):
    builder = DeviceBuilder(logger=logging.getLogger("test_builder"))
    communicator = _communicator_mock()
    serial_communicator_factory = Mock(return_value=communicator)
    monkeypatch.setattr(builder_module, "SerialCommunicator", serial_communicator_factory)

    amp = _device_mock(DeviceType.DESCALE, supports_start_configurator=True)
    amp.restart = AsyncMock(side_effect=RuntimeError("permission denied"))
    builder.build_amp = AsyncMock(return_value=amp)  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="permission denied"):
        await builder.build_configurator(Mock())

    amp.disconnect.assert_not_called()


@pytest.mark.asyncio
async def test_build_configurator_raises_when_device_cannot_switch(monkeypatch):
    builder = DeviceBuilder(logger=logging.getLogger("test_builder"))
    communicator = _communicator_mock()
    serial_communicator_factory = Mock(return_value=communicator)
    monkeypatch.setattr(builder_module, "SerialCommunicator", serial_communicator_factory)

    amp = _device_mock(DeviceType.DESCALE, supports_start_configurator=False)
    builder.build_amp = AsyncMock(return_value=amp)  # type: ignore[method-assign]

    with pytest.raises(ConnectionError, match="start_configurator"):
        await builder.build_configurator(Mock())

    communicator.open_communication.assert_awaited_once()
    amp.execute_command.assert_not_called()
    amp.disconnect.assert_not_called()