

from typing import List
from sonic_protocol.command_codes import CommandCode
from sonic_protocol.defs import AnswerDef, AnswerFieldDef, CommandContract, CommandDef, CommandParamDef, FieldType, SonicTextCommandAttrs, UserManualAttrs
from sonic_protocol.protocols.protocol_v1_0_0.transducer_commands.transducer_fields import param_frequency, param_gain
from sonic_protocol.field_names import EFieldName

field_unknown_answer = AnswerFieldDef(
	field_name=EFieldName.UNKNOWN_ANSWER,
	field_type=FieldType(str)
)


unknown_set_frequency = CommandContract(
    code=CommandCode.SET_FREQ,
    command_def=CommandDef(
        index_param=None,
        setter_param=param_frequency,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!f", "!freq", "!frequency", "set_frequency"]
        )
    ),
    answer_def=AnswerDef(fields=[field_unknown_answer]),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the frequency of the transducer on the device."
    ),
    is_release=True,
    tags=["frequency", "transducer"]
)

unknown_get_frequency = CommandContract(
    code=CommandCode.GET_FREQ,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?f", "?freq", "?frequency", "get_frequency"]
        )
    ),
    answer_def=AnswerDef(fields=[field_unknown_answer]),
    user_manual_attrs=UserManualAttrs(
        description="Command to get the frequency of the transducer on the device."
    ),
    is_release=True,
    tags=["frequency", "transducer"]
)

unknown_get_transducer = CommandContract(
    code=CommandCode.GET_TRANSDUCER_ID,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?transducer", "?tdr", "?transducer_id", "?tdr_id"] 
        )
    ),
    answer_def=AnswerDef(fields=[field_unknown_answer]),
    user_manual_attrs=UserManualAttrs(
        description="Command to get ID of the transducer connected to the device"
    ),
    is_release=True,
    tags=["transducer"]
)

unknown_set_transducer = CommandContract(
    code=CommandCode.SET_TRANSDUCER_ID,
    command_def=CommandDef(
        index_param=None,
        setter_param=CommandParamDef(
            name=EFieldName.TRANSDUCER_ID,
            param_type=FieldType(str)
        ),
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!transducer", "!tdr", "!transducer_id", "!tdr_id"]
        )
    ),
    answer_def=AnswerDef(fields=[field_unknown_answer]),
    user_manual_attrs=UserManualAttrs(
        description="Command to set ID of the transducer connected to the device"
    ),
    is_release=True,
    tags=["transducer"]
)


unknown_set_gain = CommandContract(
    code=CommandCode.SET_GAIN,
    command_def=CommandDef(
        index_param=None,
        setter_param=param_gain,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!g", "!gain", "set_gain"]
        )
    ),
    answer_def=AnswerDef(fields=[field_unknown_answer]),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the gain of the transducer on the device."
    ),
    is_release=True,
    tags=["gain", "transducer"],
)

unknown_get_gain = CommandContract(
    code=CommandCode.GET_GAIN,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?g", "?gain", "get_gain"]
        )
    ),
    answer_def=AnswerDef(fields=[field_unknown_answer]),
    user_manual_attrs=UserManualAttrs(
        description="Command to get the gain of the transducer on the device."
    ),
    is_release=True,
    tags=["gain", "transducer"]
)

unknown_set_on = CommandContract(
    code=CommandCode.SET_ON,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!ON", "set_on"]
        )
    ),
    answer_def=AnswerDef(fields=[field_unknown_answer]),
    user_manual_attrs=UserManualAttrs(
        description="Command to turn the transducer on."
    ),
    is_release=True,
    tags=["transducer"]
)

unknown_set_off = CommandContract(
    code=CommandCode.SET_OFF,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!OFF", "set_off"]
        )
    ),
    answer_def=AnswerDef(fields=[field_unknown_answer]),
    user_manual_attrs=UserManualAttrs(
        description="Command to turn the transducer off."
    ),
    is_release=True,
    tags=["transducer"]
)

unknown_command_contract_list: List[CommandContract]  = [
    unknown_get_frequency,
    unknown_set_frequency,
    unknown_get_transducer,
    unknown_set_transducer,
    unknown_set_on,
    unknown_set_off,
    unknown_get_gain,
    unknown_set_gain,
]