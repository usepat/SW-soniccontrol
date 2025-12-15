

from sonic_protocol.field_names import EFieldName
from sonic_protocol.schema import Anomaly, AnswerFieldDef, ControlMode, ConverterType, FieldType, SIPrefix, SIUnit, SonicTextAnswerFieldAttrs, SystemState, TransducerState

from ..types import types as t
import numpy as np

snr_field = AnswerFieldDef(
    field_name=EFieldName.SNR,
    field_type=FieldType(str)
)

field_type_control_mode = FieldType(
    field_type=ControlMode, 
    converter_ref=ConverterType.ENUM
)
field_control_mode = AnswerFieldDef(
    field_name=EFieldName.CONTROL_MODE,
    field_type=field_type_control_mode
)

error_message_field = AnswerFieldDef(EFieldName.ERROR_MESSAGE, FieldType(str))

field_type_dac_voltage = FieldType(
    field_type=float,
    min_value=0,
    max_value=3.3, 
    si_unit=SIUnit.VOLTAGE,
    si_prefix=SIPrefix.NONE,
)

field_dac_voltage = AnswerFieldDef(
    field_name=EFieldName.VOLTAGE,
    field_type=field_type_dac_voltage,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(
        prefix="DAC Voltage: "
    )
)

field_anomaly_detection = AnswerFieldDef(
    field_name=EFieldName.ANOMALY_DETECTION,
    field_type=FieldType(field_type=Anomaly, converter_ref=ConverterType.ENUM),
)

field_transducer_state = AnswerFieldDef(
    field_name=EFieldName.TRANSDUCER_STATE,
    field_type=FieldType(TransducerState, converter_ref=ConverterType.ENUM),
)

field_system_state = AnswerFieldDef(
    field_name=EFieldName.SYSTEM_STATE,
    field_type=FieldType(SystemState, converter_ref=ConverterType.ENUM),
)

field_type_device_state = FieldType(
    field_type=t.DeviceState,
    converter_ref=ConverterType.ENUM
)

field_device_state = AnswerFieldDef(
    EFieldName.DEVICE_TYPE, 
    field_type_device_state, 
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="device state: ")
)

field_minutes = AnswerFieldDef(
    EFieldName.MINUTES, 
    field_type=FieldType(field_type=np.uint8), 
    sonic_text_attrs=SonicTextAnswerFieldAttrs(postfix="m")
)

field_hours = AnswerFieldDef(
    EFieldName.HOURS, 
    field_type=FieldType(field_type=np.uint8), 
    sonic_text_attrs=SonicTextAnswerFieldAttrs(postfix="h")
)

field_days = AnswerFieldDef(
    EFieldName.DAYS, 
    field_type=FieldType(field_type=np.uint32), 
    sonic_text_attrs=SonicTextAnswerFieldAttrs(postfix="d")
)