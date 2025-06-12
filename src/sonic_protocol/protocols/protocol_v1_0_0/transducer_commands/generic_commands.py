from sonic_protocol.defs import (
	CommandCode, FieldType, SonicTextCommandAttrs, UserManualAttrs, CommandDef, AnswerDef, 
    CommandParamDef, CommandContract
)
from sonic_protocol.protocols.protocol_v1_0_0.transducer_commands.transducer_fields import (
    field_transducer, param_gain, field_gain, field_signal, field_temperature_kelvin
)
from sonic_protocol.field_names import EFieldName

get_transducer = CommandContract(
    code=CommandCode.GET_TRANSDUCER_ID,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?transducer", "?tdr", "?transducer_id", "?tdr_id"] 
        )
    ),
    answer_def=AnswerDef(fields=[field_transducer]),
    user_manual_attrs=UserManualAttrs(
        description="Command to get ID of the transducer connected to the device"
    ),
    is_release=True,
    tags=["transducer"]
)

set_transducer = CommandContract(
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
    answer_def=AnswerDef(fields=[field_transducer]),
    user_manual_attrs=UserManualAttrs(
        description="Command to set ID of the transducer connected to the device"
    ),
    is_release=True,
    tags=["transducer"]
)



set_gain = CommandContract(
    code=CommandCode.SET_GAIN,
    command_def=CommandDef(
        index_param=None,
        setter_param=param_gain,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!g", "!gain", "set_gain"]
        )
    ),
    answer_def=AnswerDef(fields=[field_gain]),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the gain of the transducer on the device."
    ),
    is_release=True,
    tags=["gain", "transducer"],
)

get_gain = CommandContract(
    code=CommandCode.GET_GAIN,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?g", "?gain", "get_gain"]
        )
    ),
    answer_def=AnswerDef(fields=[field_gain]),
    user_manual_attrs=UserManualAttrs(
        description="Command to get the gain of the transducer on the device."
    ),
    is_release=True,
    tags=["gain", "transducer"]
)

set_on = CommandContract(
    code=CommandCode.SET_ON,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!ON", "set_on"]
        )
    ),
    answer_def=AnswerDef(fields=[field_signal]),
    user_manual_attrs=UserManualAttrs(
        description="Command to turn the transducer on."
    ),
    is_release=True,
    tags=["transducer"]
)

set_off = CommandContract(
    code=CommandCode.SET_OFF,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!OFF", "set_off"]
        )
    ),
    answer_def=AnswerDef(fields=[field_signal]),
    user_manual_attrs=UserManualAttrs(
        description="Command to turn the transducer off."
    ),
    is_release=True,
    tags=["transducer"]
)

get_temp = CommandContract(
    code=CommandCode.GET_TEMP,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?temp", "?temperature", "get_temperature"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_temperature_kelvin]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to get the temperature of the device in celsiuus."
    ),
    is_release=True,
    tags=["temperature", "transducer"]
)


transducer_generic_command_contract_list = [
    get_transducer,
    set_gain,
    get_gain,
    set_on,
    set_off,
    get_transducer,
    set_transducer,
    get_temp
]