from typing import Any, Dict, List
from pytest_check.context_manager import check
from sonic_protocol.command_codes import CommandCode
from soniccontrol import Answer, EFieldName
from soniccontrol import Command
from soniccontrol.remote_controller import RemoteController


def assert_answer(answer: Answer, expected_fields: Dict[EFieldName, Any], should_be_valid: bool = True):
    assert answer.valid == should_be_valid, f"Answer should be {should_be_valid}, but is {answer.valid}"

    with check:
        for field_name, value in expected_fields.items():
            assert field_name in answer.field_value_dict, f"The answer does not contain the field with name {field_name.name}"
            assert answer.field_value_dict[field_name] == value, "The field of the answer has a different value than expected"
        

def assert_answer_is_not_error(answer: Answer, errors_to_check: List[CommandCode] | None = None):
    # TODO: think about how to design this function properly
    if answer.is_error_msg:
        if errors_to_check is not None:
            assert answer.command_code not in errors_to_check, "Significant error occured"
        else:
            assert answer.is_error_msg, "Answer is an error"
    else:
        assert answer.valid, "answer is not valid and not an error"


async def send_command_and_check_response(controller: RemoteController, command: str | Command) -> Answer:
    answer = await controller.send_command(command)
    assert_answer_is_not_error(answer, errors_to_check=[
        CommandCode.E_INTERNAL_DEVICE_ERROR, 
        CommandCode.E_COMMAND_NOT_KNOWN, 
        CommandCode.E_PARSING_ERROR, 
        CommandCode.E_SYNTAX_ERROR
    ])
    return answer
