from typing import List
from sonic_protocol.schema import (
	SonicTextCommandAttrs, UserManualAttrs, CommandDef, AnswerDef, CommandContract
)
from sonic_protocol.protocols.protocol_v1_0_0.transducer_commands.transducer_fields import (
    param_frequency, field_frequency, field_temperature_kelvin, field_urms, field_irms, field_phase, field_ts_flag,
    param_index, field_atf, param_atf, field_att, param_att, field_atk, param_atk, param_waveform, field_waveform,
    field_signal, field_gain
)

from sonic_protocol.protocols.protocol_v1_0_0.procedure_commands.procedure_fields import (
    field_procedure
)
from sonic_protocol.protocols.protocol_v1_0_0.generic_commands.generic_fields import (
    error_code_field
)
from sonic_protocol.protocols.protocol_v1_0_0.unknown_commands.unknown_commands import field_unknown_answer

from sonic_protocol.command_codes import CommandCode

set_frequency = CommandContract(
    code=CommandCode.SET_FREQ,
    command_def=CommandDef(
        index_param=None,
        setter_param=param_frequency,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!f", "!freq", "!frequency", "set_frequency"]
        )
    ),
    answer_def=AnswerDef(fields=[field_frequency]),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the frequency of the transducer on the device."
    ),
    is_release=True,
    tags=["frequency", "transducer"]
)

get_frequency = CommandContract(
    code=CommandCode.GET_FREQ,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?f", "?freq", "?frequency", "get_frequency"]
        )
    ),
    answer_def=AnswerDef(fields=[field_frequency]),
    user_manual_attrs=UserManualAttrs(
        description="Command to get the frequency of the transducer on the device."
    ),
    is_release=True,
    tags=["frequency", "transducer"]
)



# generate the command contract and the answer definition
get_uipt = CommandContract(
    code=CommandCode.GET_UIPT,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?uipt"]
        )
    ),
    answer_def=AnswerDef(
        fields=[
            field_urms,
            field_irms,
            field_phase,
            field_ts_flag
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to get voltage, current and phase of the transducer on the device."
    ),
    is_release=False,
    tags=["transducer"]
)

get_irms = CommandContract(
    code=CommandCode.GET_IRMS,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?curr", "?irms"]
        )
    ),
    answer_def=AnswerDef(
        fields=[
            field_irms,
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to get irms of the device"
    ),
    is_release=False,
    tags=["transducer", "descale"]
)


get_atf = CommandContract(
    code=CommandCode.GET_ATF,
    command_def=CommandDef(
        index_param=param_index,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?atf"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_atf]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to get the atf"
    ),
    is_release=True,
    tags=["transducer", "config"]
)

get_atf_list = CommandContract(
    code=CommandCode.GET_ATF_LIST,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?atf_list"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_unknown_answer]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to get a list of atfs"
    ),
    is_release=True,
    tags=["transducer", "config"]
)

set_atf = CommandContract(
    code=CommandCode.SET_ATF,
    command_def=CommandDef(
        index_param=param_index,
        setter_param=param_atf,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!atf"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_atf]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the atf"
    ),
    is_release=True,
    tags=["transducer", "config"]
)



get_att = CommandContract(
    code=CommandCode.GET_ATT,
    command_def=CommandDef(
        index_param=param_index,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?att"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_att]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to get the att"
    ),
    is_release=True,
    tags=["transducer", "config"]
)

get_att_list = CommandContract(
    code=CommandCode.GET_ATT_LIST,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?att_list"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_unknown_answer]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to get a list of atts"
    ),
    is_release=True,
    tags=["transducer", "config"]
)

set_att = CommandContract(
    code=CommandCode.SET_ATT,
    command_def=CommandDef(
        index_param=param_index,
        setter_param=param_att, # TODO make a better param for att
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!att"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_att]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the att"
    ),
    is_release=True,
    tags=["transducer", "config"]
)


get_atk = CommandContract(
    code=CommandCode.GET_ATK,
    command_def=CommandDef(
        index_param=param_index,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?atk"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_atk]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to get the atk"
    ),
    is_release=True,
    tags=["transducer", "config"]
)

get_atk_list = CommandContract(
    code=CommandCode.GET_ATK_LIST,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?atk_list"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_unknown_answer]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to get a list of atks"
    ),
    is_release=True,
    tags=["transducer", "config"]
)

set_atk = CommandContract(
    code=CommandCode.SET_ATK,
    command_def=CommandDef(
        index_param=param_index,
        setter_param=param_atk,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!atk"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_atk]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the atk"
    ),
    is_release=True,
    tags=["transducer", "config"]
)

set_waveform = CommandContract(
    code=CommandCode.SET_WAVEFORM,
    command_def=CommandDef(
        setter_param=param_waveform,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!waveform", "set_waveform"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_waveform]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the waveform of the transducer."
    ),
    is_release=True,
    tags=["transducer", "waveform"]
)

get_update_worker = CommandContract(
    code=CommandCode.GET_UPDATE,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["-", "get_update"]
        )
    ),
    answer_def=AnswerDef(
        fields=[
            error_code_field,
            field_frequency,
            field_gain,
            field_procedure,
            field_temperature_kelvin,
            field_urms,
            field_irms,
            field_phase,
            field_signal,
            field_ts_flag
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Mainly used by sonic control to get a short and computer friendly parsable status update."
    ),
    is_release=True,
    tags=["update", "status"]
)

transducer_command_contract_list: List[CommandContract]  = [
    get_update_worker,
    set_frequency,
    get_frequency,
    get_atf,
    get_atf_list,
    set_atf,
    get_att,
    get_att_list,
    set_att,
    get_atk,
    get_atk_list,
    set_atk,
    set_waveform,
    get_uipt
]