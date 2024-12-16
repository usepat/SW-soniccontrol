from sonic_protocol.defs import (
    CommandCode, CommunicationChannel, CommunicationProtocol, ConverterType, FieldType, InputSource, SonicTextCommandAttrs, UserManualAttrs, CommandDef, AnswerDef, CommandParamDef, 
    AnswerFieldDef, CommandContract, SonicTextAnswerFieldAttrs, Timestamp, LoggerName, Loglevel
)
from sonic_protocol.field_names import EFieldName
from sonic_protocol.command_contracts.contract_generators import create_list_with_unknown_answer_alternative


field_termination = AnswerFieldDef(
    field_name=EFieldName.TERMINATION,
    field_type=FieldType(field_type=bool, converter_ref=ConverterType.TERMINATION),
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

field_type_comm_channel = FieldType(
    field_type=CommunicationChannel, 
    converter_ref=ConverterType.ENUM
)
field_comm_channel = AnswerFieldDef(
    field_name=EFieldName.COMMUNICATION_CHANNEL,
    field_type=field_type_comm_channel,
)

set_physical_comm_channel = CommandContract(
    code=CommandCode.SET_PHYS_COM_CHANNEL,
    command_defs=CommandDef(
        setter_param=CommandParamDef(
            name=EFieldName.COMMUNICATION_CHANNEL,
            param_type=field_type_comm_channel
        ),
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!phys", "set_physical_comm_channel"]
        )
    ),
    answer_defs=AnswerDef(
        fields=[field_comm_channel]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the physical communication channel"
    ),
    is_release=True,
    tags=["communication"]
)

field_type_comm_protocol = FieldType(
    field_type=CommunicationProtocol, 
    converter_ref=ConverterType.ENUM
)
field_comm_protocol = AnswerFieldDef(
    field_name=EFieldName.COMMUNICATION_PROTOCOL,
    field_type=field_type_comm_protocol
)

set_comm_protocol = CommandContract(
    code=CommandCode.SET_COM_PROT,
    command_defs=CommandDef(
        setter_param=CommandParamDef(
            name=EFieldName.COMMUNICATION_PROTOCOL,
            param_type=field_type_comm_protocol
        ),
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!prot", "set_comm_protocol"]
        )
    ),
    answer_defs=AnswerDef(
        fields=[field_comm_protocol]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the communication protocol"
    ),
    is_release=True,
    tags=["communication", "protocol"]
)

field_type_input_source = FieldType(
    field_type=InputSource, 
    converter_ref=ConverterType.ENUM
)
field_input_source = AnswerFieldDef(
    field_name=EFieldName.INPUT_SOURCE,
    field_type=field_type_input_source
)

set_input_source = CommandContract(
    code=CommandCode.SET_INPUT_SOURCE,
    command_defs=CommandDef(
        setter_param=CommandParamDef(
            name=EFieldName.INPUT_SOURCE,
            param_type=field_type_input_source
        ),
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!input", "!input_source", "set_input_source"]
        )
    ),
    answer_defs=AnswerDef(
        fields=[field_input_source]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the input source. Where to get commands from"
    ),
    is_release=True,
    tags=["communication"]
)
param_type_timestamp = FieldType(
    field_type=Timestamp,
    converter_ref=ConverterType.TIMESTAMP
)

field_timestamp = AnswerFieldDef(
    field_name=EFieldName.TIMESTAMP,
    field_type=param_type_timestamp
)
set_datetime = CommandContract(
    code=CommandCode.SET_DATETIME,
    command_defs=CommandDef(
        setter_param=CommandParamDef(
            name=EFieldName.TIMESTAMP,
            param_type=param_type_timestamp
        ),
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!datetime", "set_datetime"]
        )
    ),
    answer_defs=AnswerDef(
        fields=[field_timestamp]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the datetime"
    ),
    is_release=True,
    tags=["datetime"]
)

get_datetime = CommandContract(
    code=CommandCode.GET_DATETIME,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?datetime", "get_datetime"]
        )
    ),
    answer_defs=AnswerDef(
        fields=[field_timestamp]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to get the datetime"
    ),
    is_release=True,
    tags=["datetime"]
)

get_datetime_pico = CommandContract(
    code=CommandCode.GET_DATETIME_PICO,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?datetime_pico", "get_datetime_pico"]
        )
    ),
    answer_defs=AnswerDef(
        fields=[field_timestamp]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to get the datetime from the rp2040"
    ),
    is_release=True,
    tags=["datetime"]
)

set_log_level = CommandContract(
    code=CommandCode.SET_LOG_LEVEL,
    command_defs=CommandDef(
        index_param=CommandParamDef(
            name=EFieldName.LOGGER_NAME,
            param_type=FieldType(
                field_type=LoggerName,
                converter_ref=ConverterType.ENUM,
            )
        ),
        setter_param=CommandParamDef(
            name=EFieldName.LOG_LEVEL,
            param_type=FieldType(
                field_type=Loglevel,
                converter_ref=ConverterType.ENUM
            )
        ),
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!log", "set_log_level"]
        )
    ),
    answer_defs=AnswerDef(
        fields=[
            AnswerFieldDef(
                field_name=EFieldName.LOGGER_NAME,
                field_type=FieldType(
                    field_type=LoggerName,
                    converter_ref=ConverterType.ENUM
                ),
                sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Set ", postfix=" log level to \\") # Escape the # character
            ),
            AnswerFieldDef(
                field_name=EFieldName.LOG_LEVEL,
                field_type=FieldType(
                    field_type=Loglevel,
                    converter_ref=ConverterType.ENUM
                )   
            )
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the log level"
    ),
    is_release=True,
    tags=["log"]
)