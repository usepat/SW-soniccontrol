from typing import List
from sonic_protocol.groups import GROUPS
from sonic_protocol.schema import (
	SonicTextCommandAttrs, UserManualAttrs, CommandDef, AnswerDef, CommandContract
)
from sonic_protocol.protocols.protocol_v1_0_0.transducer_commands.transducer_fields import (
    param_swf, field_swf, field_gain, field_temperature_kelvin, field_irms, field_signal
)
from sonic_protocol.protocols.protocol_v1_0_0.transducer_commands.transducer_commands import (
    get_irms
)
from sonic_protocol.protocols.protocol_v1_0_0.procedure_commands.procedure_fields import (
    field_procedure
)

from sonic_protocol.protocols.protocol_v1_0_0.generic_commands.generic_fields import (
    error_code_field
)

from sonic_protocol.command_codes import CommandCode

set_swf = CommandContract(
    code=CommandCode.SET_SWF,
    command_def=CommandDef(
        index_param=None,
        setter_param=param_swf,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!swf", "set_switching_frequency"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_swf]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Sets the transducer switching frequency on the device."
    ),
    is_release=True,
    group_id=GROUPS.transducer,
    tags=["switching frequency", "transducer"]
)

get_swf = CommandContract(
    code=CommandCode.GET_SWF,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?swf", "get_switching_frequency"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_swf]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Retrieves the transducer switching frequency from the device."
    ),
    is_release=True,
    group_id=GROUPS.transducer,
    tags=["switching frequency", "transducer"]
)

get_update_descale = CommandContract(
    code=CommandCode.GET_UPDATE,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["-", "get_update"]
        )
    ),
    answer_def=AnswerDef(
        fields=[
            error_code_field,
            field_swf,
            field_gain,
            field_procedure,
            field_temperature_kelvin,
            field_irms,
            field_signal,
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Primarily used by Sonic Control to retrieve a compact, machine-readable status update."
    ),
    is_release=True,
    group_id=GROUPS.measurements,
    tags=["update", "status"]
)

descale_command_contract_list: List[CommandContract]  =  [
    get_update_descale,
    set_swf,
    get_swf,
    get_irms
] 