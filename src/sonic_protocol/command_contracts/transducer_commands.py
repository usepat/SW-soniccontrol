import numpy as np
from sonic_protocol.command_contracts.contract_generators import create_list_with_unknown_answer_alternative
from sonic_protocol.defs import (
	CommandCode, DeviceParamConstantType, FieldType, SonicTextCommandAttrs, UserManualAttrs, CommandDef, AnswerDef, CommandParamDef, 
	AnswerFieldDef, CommandContract
)
from sonic_protocol.field_names import EFieldName
from sonic_protocol.command_contracts.fields import (
    field_unknown_answer, field_type_frequency, field_type_temperature_celsius,
    field_frequency, field_gain, field_signal, field_swf,
    field_type_gain, swf_field_type, field_temperature_kelvin,
    field_urms, field_irms, field_phase, field_ts_flag
)


param_frequency = CommandParamDef(
    name=EFieldName.FREQUENCY,
    param_type=field_type_frequency,
    user_manual_attrs=UserManualAttrs(
        description="Frequency of the transducer"
    )
)

set_frequency = CommandContract(
    code=CommandCode.SET_FREQ,
    command_defs=CommandDef(
        index_param=None,
        setter_param=param_frequency,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!f", "!freq", "!frequency", "set_frequency"]
        )
    ),
    answer_defs=create_list_with_unknown_answer_alternative(
        AnswerDef(fields=[field_frequency])
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the frequency of the transducer on the device."
    ),
    is_release=True,
    tags=["frequency", "transducer"]
)

get_frequency = CommandContract(
    code=CommandCode.GET_FREQ,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?f", "?freq", "?frequency", "get_frequency"]
        )
    ),
    answer_defs=create_list_with_unknown_answer_alternative(
        AnswerDef(fields=[field_frequency])
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to get the frequency of the transducer on the device."
    ),
    is_release=True,
    tags=["frequency", "transducer"]
)

param_gain = CommandParamDef(
    name=EFieldName.GAIN,
    param_type=field_type_gain,
    user_manual_attrs=UserManualAttrs(
        description="Gain of the transducer"
    )
)

set_gain = CommandContract(
    code=CommandCode.SET_GAIN,
    command_defs=CommandDef(
        index_param=None,
        setter_param=param_gain,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!g", "!gain", "set_gain"]
        )
    ),
    answer_defs=create_list_with_unknown_answer_alternative(
        AnswerDef(fields=[field_gain])
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the gain of the transducer on the device."
    ),
    is_release=True,
    tags=["gain", "transducer"],
)

get_gain = CommandContract(
    code=CommandCode.GET_GAIN,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?g", "?gain", "get_gain"]
        )
    ),
    answer_defs=create_list_with_unknown_answer_alternative(
        AnswerDef(fields=[field_gain])
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to get the gain of the transducer on the device."
    ),
    is_release=True,
    tags=["gain", "transducer"]
)

set_on = CommandContract(
    code=CommandCode.SET_ON,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!ON", "set_on"]
        )
    ),
    answer_defs=create_list_with_unknown_answer_alternative(
        AnswerDef(fields=[field_signal])
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to turn the transducer on."
    ),
    is_release=True,
    tags=["transducer"]
)

set_off = CommandContract(
    code=CommandCode.SET_OFF,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!OFF", "set_off"]
        )
    ),
    answer_defs=create_list_with_unknown_answer_alternative(
        AnswerDef(fields=[field_signal])
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to turn the transducer off."
    ),
    is_release=True,
    tags=["transducer"]
)

param_swf = CommandParamDef(
    name=EFieldName.SWF,
    param_type=swf_field_type,
    user_manual_attrs=UserManualAttrs(
        description="Switching frequency of the transducer"
    )
)

set_swf = CommandContract(
    code=CommandCode.SET_SWF,
    command_defs=CommandDef(
        index_param=None,
        setter_param=param_swf,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!swf", "set_switching_frequency"]
        )
    ),
    answer_defs=AnswerDef(
        fields=[field_swf]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the switching frequency of the transducer on the device."
    ),
    is_release=False,
    tags=["switching frequency", "transducer"]
)

get_swf = CommandContract(
    code=CommandCode.GET_SWF,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?swf", "get_switching_frequency"]
        )
    ),
    answer_defs=AnswerDef(
        fields=[field_swf]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to get the switching frequency of the transducer on the device."
    ),
    is_release=False,
    tags=["switching frequency", "transducer"]
)

param_temp_celsius = CommandParamDef(
    name=EFieldName.TEMPERATURE,
    param_type=field_type_temperature_celsius,
    user_manual_attrs=UserManualAttrs(
        description="Temperature of the device in celsius"
    )
)

get_temp = CommandContract(
    code=CommandCode.GET_TEMP,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?temp", "?temperature", "get_temperature"]
        )
    ),
    answer_defs=AnswerDef(
        fields=[field_temperature_kelvin]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to get the temperature of the device in celsiuus."
    ),
    is_release=True,
    tags=["temperature", "transducer"]
)

# generate the command contract and the answer definition
get_uipt = CommandContract(
    code=CommandCode.GET_UIPT,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?uipt"]
        )
    ),
    answer_defs=AnswerDef(
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

param_index = CommandParamDef(
    name=EFieldName.INDEX,
    param_type=FieldType(
        field_type=np.uint8,
        min_value=DeviceParamConstantType.MIN_TRANSDUCER_INDEX,
        max_value=DeviceParamConstantType.MAX_TRANSDUCER_INDEX,
    )
)
param_atf = CommandParamDef(
    name=EFieldName.ATF,
    param_type=field_type_frequency
)

param_att = CommandParamDef(
    name=EFieldName.ATT,
    param_type=field_type_temperature_celsius
)

field_type_atk = FieldType(
    float,
    min_value=-10000000,
    max_value=+10000000
)

param_atk = CommandParamDef(
    name=EFieldName.ATK,
    param_type=field_type_atk
)

field_atf = AnswerFieldDef(
    field_name=EFieldName.ATF,
    field_type=field_type_frequency
)

get_atf = CommandContract(
    code=CommandCode.GET_ATF,
    command_defs=CommandDef(
        index_param=param_index,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?atf"]
        )
    ),
    answer_defs=AnswerDef(
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
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?atf_list"]
        )
    ),
    answer_defs=AnswerDef(
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
    command_defs=CommandDef(
        index_param=param_index,
        setter_param=param_atf,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!atf"]
        )
    ),
    answer_defs=AnswerDef(
        fields=[field_atf]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the atf"
    ),
    is_release=True,
    tags=["transducer", "config"]
)

field_att = AnswerFieldDef(
    field_name=EFieldName.ATT,
    field_type=field_type_temperature_celsius
)

get_att = CommandContract(
    code=CommandCode.GET_ATT,
    command_defs=CommandDef(
        index_param=param_index,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?att"]
        )
    ),
    answer_defs=AnswerDef(
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
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?att_list"]
        )
    ),
    answer_defs=AnswerDef(
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
    command_defs=CommandDef(
        index_param=param_index,
        setter_param=param_att, # TODO make a better param for att
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!att"]
        )
    ),
    answer_defs=AnswerDef(
        fields=[field_att]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the att"
    ),
    is_release=True,
    tags=["transducer", "config"]
)

field_atk = AnswerFieldDef(
    field_name=EFieldName.ATK,
    field_type=field_type_atk
)

get_atk = CommandContract(
    code=CommandCode.GET_ATK,
    command_defs=CommandDef(
        index_param=param_index,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?atk"]
        )
    ),
    answer_defs=AnswerDef(
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
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?atk_list"]
        )
    ),
    answer_defs=AnswerDef(
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
    command_defs=CommandDef(
        index_param=param_index,
        setter_param=param_atk,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!atk"]
        )
    ),
    answer_defs=AnswerDef(
        fields=[field_atk]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the atk"
    ),
    is_release=True,
    tags=["transducer", "config"]
)
