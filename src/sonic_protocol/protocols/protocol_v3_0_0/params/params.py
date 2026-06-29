import numpy as np
from sonic_protocol.field_names import EFieldName
from sonic_protocol.schema import CommandParamDef, FieldType, UserManualAttrs

from ..fields import fields as f

# template_param = CommandParamDef(
#     name=EFieldName.{field_name},
#     param_type=f.template_field_type
# )


param_index_uint8 = CommandParamDef(
    name=EFieldName.INDEX,
    param_type=FieldType(field_type=np.uint8, min_value=np.uint8(0))
)

param_dac_mV = CommandParamDef(
    name=EFieldName.VOLTAGE,
    param_type=f.field_type_dac_mV
)

