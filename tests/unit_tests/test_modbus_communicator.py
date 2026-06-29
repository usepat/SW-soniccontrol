from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from sonic_protocol.python_parser.commands import SetGain
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

    assert not answer.valid
    assert answer.message == "Modbus communicator is not connected"
