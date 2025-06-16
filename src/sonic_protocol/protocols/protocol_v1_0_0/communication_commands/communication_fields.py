from sonic_protocol.defs import (CommunicationProtocol, InputSource,  FieldType, 
	AnswerFieldDef, CommunicationChannel, ConverterType
)
from sonic_protocol.field_names import EFieldName


field_termination = AnswerFieldDef(
    field_name=EFieldName.TERMINATION,
    field_type=FieldType(field_type=bool, converter_ref=ConverterType.TERMINATION),
)


field_type_comm_channel = FieldType(
    field_type=CommunicationChannel, 
    converter_ref=ConverterType.ENUM
)
field_comm_channel = AnswerFieldDef(
    field_name=EFieldName.COMMUNICATION_CHANNEL,
    field_type=field_type_comm_channel,
)

field_type_comm_protocol = FieldType(
    field_type=CommunicationProtocol, 
    converter_ref=ConverterType.ENUM
)
field_comm_protocol = AnswerFieldDef(
    field_name=EFieldName.COMMUNICATION_PROTOCOL,
    field_type=field_type_comm_protocol
)

field_type_input_source = FieldType(
    field_type=InputSource, 
    converter_ref=ConverterType.ENUM
)
field_input_source = AnswerFieldDef(
    field_name=EFieldName.INPUT_SOURCE,
    field_type=field_type_input_source
)