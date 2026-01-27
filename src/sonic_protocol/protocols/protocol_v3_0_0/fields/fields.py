

from sonic_protocol.field_names import EFieldName
from sonic_protocol.schema import Anomaly, AnswerFieldDef, ControlMode, ConverterType, DeviceParamConstantType, FieldType, SIPrefix, SIUnit, SonicTextAnswerFieldAttrs, SystemState, TransducerState

from ..types import types as t
import numpy as np

from sonic_protocol.protocols.protocol_v1_0_0.transducer_commands.transducer_fields import (
    field_type_gain
)

#from ...protocol_v1_0_0.transducer_commands import transducer_fields as tf

irms_field_type = FieldType(
    field_type=np.uint16,
    si_unit=SIUnit.AMPERE,
    si_prefix=SIPrefix.MILLI,
)

irms_field = AnswerFieldDef(
    EFieldName.IRMS, 
    field_type=irms_field_type, 
    sonic_text_attrs=SonicTextAnswerFieldAttrs()
)

urms_field_type = FieldType(
    field_type=np.uint16,
    si_unit=SIUnit.VOLTAGE,
    si_prefix=SIPrefix.MILLI,
)

urms_field = AnswerFieldDef(
    field_name=EFieldName.URMS,
    field_type=urms_field_type
)

phase_field_type = FieldType(
    field_type=np.uint16,
    si_unit=SIUnit.DEGREE,
    si_prefix=SIPrefix.CENTI,
)

phase_field = AnswerFieldDef(
    field_name=EFieldName.PHASE,
    field_type=phase_field_type
)

ts_flag_field_type = FieldType(
    field_type=np.uint16,
    si_unit=SIUnit.VOLTAGE,
    si_prefix=SIPrefix.MILLI,
)

ts_flag_field = AnswerFieldDef(
    field_name=EFieldName.TS_FLAG,
    field_type=ts_flag_field_type
)


field_type_frequency = FieldType(
    field_type=np.uint16,
    si_unit=SIUnit.HERTZ,
    si_prefix=SIPrefix.HECTO,
	max_value=DeviceParamConstantType.MAX_FREQUENCY,
	min_value=DeviceParamConstantType.MIN_FREQUENCY,
)

frequency_field = AnswerFieldDef(
    field_name=EFieldName.FREQUENCY,
    field_type=field_type_frequency,
)

# TODO ask Stefan Radel if we need 1Hz resolution for atfs, this would be fine I guess

field_type_atf = FieldType(
    field_type=np.uint16,
    si_unit=SIUnit.HERTZ,
    si_prefix=SIPrefix.HECTO,
	max_value=DeviceParamConstantType.MAX_FREQUENCY,
	min_value=DeviceParamConstantType.MIN_FREQUENCY,
    allowed_values=(np.uint16(0),)
)

atf_field = AnswerFieldDef(
    field_name=EFieldName.ATF,
    field_type=field_type_atf
)


field_ramp_f_start = AnswerFieldDef(
    field_name=EFieldName.RAMP_F_START,
    field_type=field_type_frequency,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Start: ")
)

field_ramp_f_stop = AnswerFieldDef(
    field_name=EFieldName.RAMP_F_STOP,
    field_type=field_type_frequency,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Stop: ")
)

field_ramp_gain = AnswerFieldDef(
    field_name=EFieldName.RAMP_GAIN,
    field_type=field_type_gain,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Gain: ")
)

## Raw field types(before calibration)
raw_measurement_field_type = FieldType(
    field_type=np.uint32,
    si_unit=SIUnit.VOLTAGE,
    si_prefix=SIPrefix.MICRO,
)
raw_urms_field = AnswerFieldDef(
    field_name=EFieldName.URMS,
    field_type=raw_measurement_field_type
)

raw_irms_field = AnswerFieldDef(
    field_name=EFieldName.IRMS,
    field_type=raw_measurement_field_type
)

raw_phase_field = AnswerFieldDef(
    field_name=EFieldName.PHASE,
    field_type=raw_measurement_field_type
)

raw_tsflag_field = AnswerFieldDef(
    field_name=EFieldName.TS_FLAG,
    field_type=raw_measurement_field_type
)

connection_status_field = AnswerFieldDef(
    field_name=EFieldName.IS_CONNECTED,
    field_type=FieldType(bool),
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="connected: ")
)

count_field = AnswerFieldDef(
    field_name=EFieldName.COUNT,
    field_type=FieldType(np.uint8)
)

test_name_field = AnswerFieldDef(
    field_name=EFieldName.TEST_NAME,
    field_type=FieldType(str)
)

test_suite_name_field = AnswerFieldDef(
    field_name=EFieldName.TEST_SUITE_NAME,
    field_type=FieldType(str)
)
