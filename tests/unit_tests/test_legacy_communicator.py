from unittest.mock import Mock

import pytest

from sonic_protocol.command_codes import CommandCode
from sonic_protocol.schema import AnswerDef, CommandContract, CommandDef, Protocol, SonicTextCommandAttrs
from soniccontrol.communication.legacy_communicator import LegacyCommunicator


def make_command(code: CommandCode, identifiers: str | list[str]) -> CommandContract:
    return CommandContract(
        code=code,
        command_def=CommandDef(sonic_text_attrs=SonicTextCommandAttrs(identifiers)),
        answer_def=AnswerDef(fields=[]),
    )


@pytest.mark.parametrize(
    ("identifiers", "request_str", "expected"),
    [
        ("?info", "?info", CommandCode.GET_INFO),
        (["?info", "?i"], "?info", CommandCode.GET_INFO),
        (["?info", "?i"], "?i", CommandCode.GET_INFO),
        ("?info", "prefix ?info\n", CommandCode.GET_INFO),
        ("!gain", "!gain=50", CommandCode.GET_INFO),
        ("?info", "?unknown", -1),
        ("?info", "?INFO", -1),
        ("?info", "?inf", -1),
        ("?info", "", -1),
        ([], "?info", -1),
    ],
)
def test_deduce_command_code_matches_identifiers(identifiers, request_str, expected):
    protocol = Mock(spec=Protocol)
    protocol.command_contracts = {
        CommandCode.GET_INFO: make_command(CommandCode.GET_INFO, identifiers),
    }
    communicator = LegacyCommunicator(protocol=protocol)

    assert communicator.deduce_command_code(request_str) == expected


def test_deduce_command_code_skips_missing_contracts_and_definitions():
    protocol = Mock(spec=Protocol)
    protocol.command_contracts = {
        CommandCode.LEGACY_PVAL: None,
        CommandCode.GET_INFO: CommandContract(
            code=CommandCode.GET_INFO,
            command_def=None,
            answer_def=AnswerDef(fields=[]),
        ),
    }
    communicator = LegacyCommunicator(protocol=protocol)

    assert communicator.deduce_command_code("?info") == -1


def test_deduce_command_code_returns_zero_for_empty_protocol():
    protocol = Mock(spec=Protocol)
    protocol.command_contracts = {}
    communicator = LegacyCommunicator(protocol=protocol)

    assert communicator.deduce_command_code("?info") == -1


def test_deduce_command_code_uses_first_matching_contract():
    protocol = Mock(spec=Protocol)
    protocol.command_contracts = {
        CommandCode.GET_INFO: make_command(CommandCode.GET_INFO, "?"),
        CommandCode.LEGACY_PVAL: make_command(CommandCode.LEGACY_PVAL, "?info"),
    }
    communicator = LegacyCommunicator(protocol=protocol)

    assert communicator.deduce_command_code("?info") == CommandCode.GET_INFO