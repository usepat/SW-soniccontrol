from typing import List
from sonic_protocol.defs import (
    CommandCode, ConverterType, FieldType, SonicTextCommandAttrs, UserManualAttrs, CommandDef, 
    AnswerDef, CommandParamDef, AnswerFieldDef, CommandContract, SonicTextAnswerFieldAttrs, LoggerName, Loglevel
)
from sonic_protocol.protocols.protocol_v1_0_0.communication_commands.communication_fields import (
    field_termination, field_type_comm_protocol, field_comm_protocol, field_type_input_source, field_input_source
)
from sonic_protocol.field_names import EFieldName




set_termination = CommandContract(
    code=CommandCode.SET_TERMINATION,
    command_def=CommandDef(
        setter_param=CommandParamDef(
            name=EFieldName.TERMINATION,
            param_type=FieldType(field_type=bool)
        ),
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!term", "set_termination"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_termination]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the 120Ohm termination resistor for rs485"
    ),
    is_release=True,
    tags=["communication", "rs485"]
)



set_comm_protocol = CommandContract(
    code=CommandCode.SET_COM_PROT,
    command_def=CommandDef(
        setter_param=CommandParamDef(
            name=EFieldName.COMMUNICATION_PROTOCOL,
            param_type=field_type_comm_protocol
        ),
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!prot", "set_comm_protocol"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_comm_protocol]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the communication protocol"
    ),
    is_release=True,
    tags=["communication", "protocol"]
)


set_input_source = CommandContract(
    code=CommandCode.SET_INPUT_SOURCE,
    command_def=CommandDef(
        setter_param=CommandParamDef(
            name=EFieldName.INPUT_SOURCE,
            param_type=field_type_input_source
        ),
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!input", "!input_source", "set_input_source"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_input_source]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the input source. Where to get commands from"
    ),
    is_release=True,
    tags=["communication"]
)



set_log_level = CommandContract(
    code=CommandCode.SET_LOG_LEVEL,
    command_def=CommandDef(
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
    answer_def=AnswerDef(
        fields=[
            AnswerFieldDef(
                field_name=EFieldName.LOGGER_NAME,
                field_type=FieldType(
                    field_type=LoggerName,
                    converter_ref=ConverterType.ENUM
                ),
                sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Set ", postfix=r" log level to \\") # Escape the # character
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

communication_command_contract_list: List[CommandContract]  = [
    set_termination,
    set_comm_protocol,
    set_input_source,
    set_log_level,
]