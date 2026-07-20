import numpy as np
from sonic_protocol.schema import Procedure, DeviceType, FieldType, AnswerFieldDef, Timestamp
from sonic_protocol.field_names import EFieldName


field_device_type = AnswerFieldDef(
	field_name=EFieldName.DEVICE_TYPE,
	field_type=FieldType(DeviceType),
)

build_date_field = AnswerFieldDef(
    field_name=EFieldName.BUILD_DATE,
    field_type=FieldType(str)
)

build_hash_field = AnswerFieldDef(
    field_name=EFieldName.BUILD_HASH,
    field_type=FieldType(str)
)


error_code_field = AnswerFieldDef(
    field_name=EFieldName.ERROR_CODE,
    field_type=FieldType(field_type=np.uint16)
)

param_type_timestamp = FieldType(
    field_type=Timestamp,
    min_value=Timestamp(
        hour= 0,
        minute= 0,
        second= 0,
        day= 1,
        month= 1,
        year= 1970
    )
)

field_timestamp = AnswerFieldDef(
    field_name=EFieldName.TIMESTAMP,
    field_type=param_type_timestamp
)

field_message = AnswerFieldDef(
    field_name=EFieldName.MESSAGE,
    field_type=FieldType(str)
)