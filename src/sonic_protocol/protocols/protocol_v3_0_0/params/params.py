from sonic_protocol.field_names import EFieldName
from sonic_protocol.schema import CommandParamDef, FieldType, UserManualAttrs

from ..fields import fields as f

# template_param = CommandParamDef(
#     name=EFieldName.{field_name},
#     param_type=f.template_field_type
# )

frequency_param = CommandParamDef(
    name=EFieldName.FREQUENCY,
    param_type=f.field_type_frequency,
    user_manual_attrs=UserManualAttrs(
        description="Frequency of the transducer"
    )
)

atf_param = CommandParamDef(
    name=EFieldName.ATF,
    param_type=f.field_type_atf
)