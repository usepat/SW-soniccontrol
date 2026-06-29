from sonic_protocol.field_names import EFieldName
from sonic_protocol.schema import CommandParamDef, FieldType

from ..fields import fields as f

password_hashed_param = CommandParamDef(
    name=EFieldName.PASSWORD_HASHED,
    param_type=FieldType(str)
)

param_dac_voltage = CommandParamDef(
    name=EFieldName.VOLTAGE,
    param_type=f.field_type_dac_voltage
)

