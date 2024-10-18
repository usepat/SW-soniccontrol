from sonic_protocol.defs import (
    CommandCode, CommunicationChannel, CommunicationProtocol, ConverterType, FieldType, InputSource, SonicTextCommandAttrs, UserManualAttrs, CommandDef, AnswerDef, CommandParamDef, 
    AnswerFieldDef, CommandContract
)

field_termination = AnswerFieldDef(
    field_path=["termination"],
    field_type=FieldType(field_type=bool),
)

set_termination = CommandContract(
    code=CommandCode.SET_TERMINATION,
    command_defs=CommandDef(
        setter_param=CommandParamDef(
            name="termination",
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
    field_path=["communication_channel"],
    field_type=field_type_comm_channel,
)

set_physical_comm_channel = CommandContract(
    code=CommandCode.SET_PHYS_COM_CHANNEL,
    command_defs=CommandDef(
        setter_param=CommandParamDef(
            name="communication_channel",
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
    field_path=["communication_protocol"],
    field_type=field_type_comm_protocol
)

set_comm_protocol = CommandContract(
    code=CommandCode.SET_PHYS_COM_CHANNEL,
    command_defs=CommandDef(
        setter_param=CommandParamDef(
            name="communication_protocol",
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
    field_path=["input_source"],
    field_type=field_type_input_source
)

set_input_source = CommandContract(
    code=CommandCode.SET_INPUT_SOURCE,
    command_defs=CommandDef(
        setter_param=CommandParamDef(
            name="input_source",
            param_type=field_type_input_source
        ),
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!input", "set_input_source"]
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

field_type_comm_channel = FieldType(
    field_type=CommunicationChannel, 
    converter_ref=ConverterType.ENUM
)
field_comm_channel = AnswerFieldDef(
    field_path=["communication_channel"],
    field_type=field_type_comm_channel,
)