from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from sonic_protocol.python_parser.commands import SetGain
from sonic_protocol.command_codes import CommandCode
from sonic_protocol.protocol import protocol_list
from sonic_protocol.schema import DeviceType, ProtocolType, Version
from soniccontrol.communication.modbus_communicator import ModbusCommunicator


def test_reset_async_serial_client_state_clears_stale_transport_bytes_and_recv_buffer():
    communicator = ModbusCommunicator()
    sync_serial = Mock()
    sync_serial.in_waiting = 3
    sync_serial.read.return_value = b"abc"
    communicator._modbus_client = SimpleNamespace(
        ctx=SimpleNamespace(
            transport=SimpleNamespace(sync_serial=sync_serial),
            recv_buffer=b"stale",
        )
    )

    communicator._reset_async_serial_client_state()

    sync_serial.read.assert_called_once_with(3)
    assert communicator._modbus_client.ctx.recv_buffer == b""


def test_reset_async_serial_client_state_without_serial_transport_still_clears_recv_buffer():
    communicator = ModbusCommunicator()
    communicator._modbus_client = SimpleNamespace(
        ctx=SimpleNamespace(
            transport=None,
            recv_buffer=b"stale",
        )
    )

    communicator._reset_async_serial_client_state()

    assert communicator._modbus_client.ctx.recv_buffer == b""


@pytest.mark.asyncio
async def test_send_command_and_validate_returns_error_when_disconnected():
    communicator = ModbusCommunicator()
    communicator._modbus_client = SimpleNamespace(connected=False)

    answer = await communicator.send_command_and_validate(Mock(), SetGain(50))

    assert not answer.is_valid
    assert answer.message == "Modbus communicator is not connected"


@pytest.mark.asyncio
@pytest.mark.parametrize("registers", [[], [0], [0, 1, 2]])
async def test_malformed_response_header_is_reported(registers):
    communicator = ModbusCommunicator()
    communicator._modbus_client = SimpleNamespace(
        read_input_registers=AsyncMock(
            return_value=SimpleNamespace(registers=registers, isError=lambda: False)
        )
    )

    response_len, error = await communicator._wait_for_response_ready()

    assert response_len == 0
    assert error == f"Invalid modbus response header length: expected 2 registers, got {len(registers)}"


@pytest.mark.asyncio
async def test_malformed_response_header_retries_command(monkeypatch, caplog):
    communicator = ModbusCommunicator()
    communicator._modbus_client = SimpleNamespace(
        connected=True,
        write_registers=AsyncMock(
            return_value=SimpleNamespace(retries=0, isError=lambda: False)
        ),
        read_input_registers=AsyncMock(side_effect=[
            SimpleNamespace(registers=[], isError=lambda: False),
            SimpleNamespace(registers=[0, 2], isError=lambda: False),
            SimpleNamespace(registers=[int(CommandCode.SET_GAIN), 50], isError=lambda: False),
        ]),
    )
    monkeypatch.setattr(communicator, "_reset_async_serial_client_state", lambda: None)
    protocol = protocol_list.build_protocol_for(
        ProtocolType(Version(3, 3, 0), DeviceType.MVP_WORKER, False)
    )

    answer = await communicator.send_command_and_validate(
        protocol.command_contracts[CommandCode.SET_GAIN], SetGain(50)
    )

    assert answer.is_valid
    assert communicator._modbus_client.write_registers.await_count == 2
    assert "Invalid modbus response header length" in caplog.text


@pytest.mark.asyncio
async def test_persistent_malformed_response_header_returns_failure(monkeypatch, caplog):
    communicator = ModbusCommunicator()
    communicator._modbus_client = SimpleNamespace(
        connected=True,
        write_registers=AsyncMock(
            return_value=SimpleNamespace(retries=0, isError=lambda: False)
        ),
        read_input_registers=AsyncMock(
            return_value=SimpleNamespace(registers=[], isError=lambda: False)
        ),
    )
    monkeypatch.setattr(communicator, "_reset_async_serial_client_state", lambda: None)
    protocol = protocol_list.build_protocol_for(
        ProtocolType(Version(3, 3, 0), DeviceType.MVP_WORKER, False)
    )

    answer = await communicator.send_command_and_validate(
        protocol.command_contracts[CommandCode.SET_GAIN], SetGain(50)
    )

    assert not answer.is_valid
    assert answer.message == "Invalid modbus response header length: expected 2 registers, got 0"
    assert communicator._modbus_client.write_registers.await_count == communicator.MAX_RETRIES
    assert "attempt 3/3 failed" in caplog.text
