from sonic_protocol.schema import (CommunicationProtocol, InputSource,  FieldType, 
	AnswerFieldDef, CommunicationChannel, Activation
)
from sonic_protocol.field_names import EFieldName


field_termination = AnswerFieldDef(
    field_name=EFieldName.TERMINATION,
    field_type=FieldType(field_type=Activation),
)


field_type_comm_channel = FieldType(
    field_type=CommunicationChannel
)
field_comm_channel = AnswerFieldDef(
    field_name=EFieldName.COMMUNICATION_CHANNEL,
    field_type=field_type_comm_channel,
)

field_type_comm_protocol = FieldType(
    field_type=CommunicationProtocol
)
field_comm_protocol = AnswerFieldDef(
    field_name=EFieldName.COMMUNICATION_PROTOCOL,
    field_type=field_type_comm_protocol
)

field_type_input_source = FieldType(
    field_type=InputSource
)
field_input_source = AnswerFieldDef(
    field_name=EFieldName.CONTROL_MODE,
    field_type=field_type_input_source
)