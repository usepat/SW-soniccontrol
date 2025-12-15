from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocols.protocol_v1_0_0.transducer_commands.transducer_fields import (
    field_type_gain
)
from sonic_protocol.schema import AnswerFieldDef, SonicTextAnswerFieldAttrs

field_wipe_gain = AnswerFieldDef(
    field_name=EFieldName.WIPE_GAIN,
    field_type=field_type_gain,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Gain: ")
)