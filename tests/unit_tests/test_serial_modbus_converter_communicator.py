import logging
from unittest.mock import AsyncMock, Mock

import pytest

from sonic_protocol.command_codes import CommandCode
from sonic_protocol.python_parser.answer import Answer, ValidationStatus
from sonic_protocol.python_parser.commands import SonicForce
from soniccontrol.communication.serial_modbus_converter_communicator import (
    SerialModbusConverterCommunicator,
)
from sonic_pytest.gui.workflows import _extract_answer_after_command


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "answer",
    [
        Answer("Force Quit Service Mode", ValidationStatus.VALID, CommandCode.SONIC_FORCE),
        Answer("", ValidationStatus.VALID, CommandCode.SONIC_FORCE),
        Answer(
            "Unknown command",
            ValidationStatus.VALID,
            CommandCode.E_COMMAND_NOT_KNOWN,
        ),
    ],
)
async def test_monitor_modbus_response_is_recognized_and_errors_are_checked(answer):
    modbus = Mock(_logger=logging.getLogger(__name__))
    modbus.send_command_and_validate = AsyncMock(return_value=answer)
    contract = Mock()
    deserializer = Mock()
    deserializer.get_command_struct.return_value = (SonicForce(), contract)
    communicator = SerialModbusConverterCommunicator(modbus, deserializer)

    response = await communicator.send_and_wait_for_response("!sonic_force")

    assert response == (
        f"{answer.command_code}#"
        f"{answer.message or communicator.EMPTY_SUCCESS_MESSAGE}"
    )
    entries = [">>> !sonic_force", response]
    if answer.is_error_msg:
        with pytest.raises(AssertionError, match="Device returned error"):
            _extract_answer_after_command(entries, 0, "!sonic_force", False)
    else:
        assert _extract_answer_after_command(entries, 0, "!sonic_force", False) == response
    assert _extract_answer_after_command(entries, 0, "!sonic_force", True) == response


@pytest.mark.asyncio
async def test_invalid_modbus_response_is_reported_as_communication_failure():
    modbus = Mock(_logger=logging.getLogger(__name__))
    modbus.send_command_and_validate = AsyncMock(
        return_value=Answer(
            "Modbus communicator is not connected",
            ValidationStatus.NOT_VALID,
            CommandCode.SONIC_FORCE,
        )
    )
    deserializer = Mock()
    deserializer.get_command_struct.return_value = (SonicForce(), Mock())
    communicator = SerialModbusConverterCommunicator(modbus, deserializer)

    with pytest.raises(RuntimeError, match="Modbus communicator is not connected"):
        await communicator.send_and_wait_for_response("!sonic_force")
