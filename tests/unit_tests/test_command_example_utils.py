from unittest.mock import Mock

import pytest

from sonic_protocol.command_codes import CommandCode
from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocols.protocol_v3_0_0.types.types import Parity, UartInterface
from sonic_protocol.python_parser.command_serializer import CommandSerializer
from sonic_protocol.schema import (
    AnswerDef,
    AnswerFieldDef,
    CommandContract,
    CommandDef,
    CommandParamDef,
    ControlMode,
    DeviceParamConstants,
    FieldType,
    Protocol,
    SonicTextCommandAttrs,
)
from sonic_protocol.user_manual_compiler.command_example_utils import (
    deduce_answer_example_for_contract,
    deduce_command_examples_for_contract,
    deduce_command_examples_for_contract_as_commands,
)
from soniccontrol.communication.modbus_communicator import ModbusCommunicator


@pytest.mark.parametrize("enum_type", [Parity, UartInterface, ControlMode])
def test_enum_examples_use_typed_members_and_wire_values(enum_type):
    field_type = FieldType(enum_type)
    contract = CommandContract(
        code=CommandCode.SET_MODBUS_PARITY,
        command_def=CommandDef(
            sonic_text_attrs=SonicTextCommandAttrs("!example"),
            setter_param=CommandParamDef(EFieldName.PARITY, field_type),
        ),
        answer_def=AnswerDef([AnswerFieldDef(EFieldName.PARITY, field_type)]),
    )
    consts = DeviceParamConstants()
    commands = deduce_command_examples_for_contract_as_commands(consts, contract)
    text_examples = deduce_command_examples_for_contract(consts, contract)
    serializer = CommandSerializer(
        Mock(spec=Protocol, command_contracts={contract.code: contract})
    )
    communicator = ModbusCommunicator()

    assert [command.args["value"] for command in commands] == list(enum_type)
    assert all(isinstance(command.args["value"], enum_type) for command in commands)
    assert text_examples == [f"!example={member.value}" for member in enum_type]
    assert [serializer.serialize_command(command) for command in commands] == text_examples
    assert [
        communicator.args_to_registers(contract, command) for command in commands
    ] == [
        [communicator.enum_member_to_firmware_value(enum_type, member)]
        for member in enum_type
    ]
    assert deduce_answer_example_for_contract(consts, contract) == (
        f"ANS#0={contract.code}#{next(iter(enum_type)).value} "
    )
