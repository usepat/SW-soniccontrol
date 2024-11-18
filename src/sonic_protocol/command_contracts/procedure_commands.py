

from sonic_protocol.command_codes import CommandCode
from sonic_protocol.defs import AnswerDef, AnswerFieldDef, CommandContract, CommandDef, CommandParamDef, FieldType, SonicTextCommandAttrs, UserManualAttrs
from sonic_protocol.field_names import EFieldName


def generate_procedure_arg_setter_contract(command_code: CommandCode, field_name: EFieldName, **kwargs) -> CommandContract:
    response_field = AnswerFieldDef(
        field_name=field_name,
        field_type=FieldType(field_type=int)
    )


field_termination = AnswerFieldDef(
    field_name=EFieldName.TERMINATION,
    field_type=FieldType(field_type=bool),
)

set_termination = CommandContract(
    code=CommandCode.SET_TERMINATION,
    command_defs=CommandDef(
        setter_param=CommandParamDef(
            name=EFieldName.TERMINATION,
            param_type=FieldType(field_type=bool)
        ),
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!term", "set_termination"]
        )
    ),
    answer_defs=AnswerDef(
        fields=[field_termination]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the 120Ohm termination resistor for rs485"
    ),
    is_release=True,
    tags=["communication", "rs485"]
)