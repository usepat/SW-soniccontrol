

from sonic_protocol.field_names import EFieldName
from sonic_protocol.schema import Anomaly, AnswerFieldDef, ControlMode, ConverterType, FieldType, SIPrefix, SIUnit, SonicTextAnswerFieldAttrs, SystemState, TransducerState

from ..types import types as t
import numpy as np


# template_field_type = FieldType(
#     field_type=t.{type/enum},
#     converter_ref=ConverterType.{converter_type}
# )

# template_answer_field = AnswerFieldDef(
#     EFieldName.{field_name}, 
#     field_type=tempalte_field_type, 
#     sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="{prefix}," postfix="{postfix}")
# )