

from typing import List
from sonic_protocol.command_codes import CommandCode
from sonic_protocol.schema import AnswerDef, AnswerFieldDef, CommandContract, CommandDef, CommandParamDef, FieldType, SonicTextAnswerFieldAttrs, SonicTextCommandAttrs, UserManualAttrs
from sonic_protocol.field_names import EFieldName
import sonic_protocol.protocols.protocol_v1_0_0.procedure_commands.procedure_fields as fields
from sonic_protocol.protocols.protocol_v1_0_0.procedure_commands.procedure_commands import generate_procedure_arg_setter_contract
from sonic_protocol.protocols.protocol_v2_0_0.procedure_commands.procedure_fields import (
    field_wipe_gain
)

get_wipe = CommandContract(
    code=CommandCode.GET_WIPE,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?wipe"]
        )
    ), 
    is_release=True,
    answer_def=AnswerDef(
        fields=[
            fields.field_wipe_f_step,
            fields.field_wipe_f_range,
            fields.field_wipe_t_on,
            fields.field_wipe_t_off,
            fields.field_wipe_t_pause,
            field_wipe_gain
        ]
    ),
    tags=["Procedure", "WIPE"]
)

wipe_proc_commands: List[CommandContract] = [
    get_wipe,
    generate_procedure_arg_setter_contract(
    CommandCode.SET_WIPE_GAIN, 
    ["!wipe_gain"], 
    response_field=field_wipe_gain, 
    )
]

all_proc_commands: List[CommandContract] = []

all_proc_commands.extend(wipe_proc_commands)

