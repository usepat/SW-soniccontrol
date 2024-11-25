import numpy as np
from sonic_protocol.defs import Procedure, DeviceParamConstantType, DeviceType, FieldType, AnswerFieldDef, CommunicationChannel, ConverterType, SIPrefix, SIUnit, SonicTextAnswerFieldAttrs, Version
from sonic_protocol.field_names import EFieldName

field_termination = AnswerFieldDef(
	field_name=EFieldName.TERMINATION,
	field_type=FieldType(field_type=bool),
)

field_type_comm_channel = FieldType(
	field_type=CommunicationChannel, 
	converter_ref=ConverterType.ENUM
)

field_device_type = AnswerFieldDef(
	field_name=EFieldName.DEVICE_TYPE,
	field_type=FieldType(DeviceType, converter_ref=ConverterType.ENUM),
)

field_type_frequency = FieldType(
    field_type=np.uint32,
    si_unit=SIUnit.HERTZ,
    #si_prefix=SIPrefix.KILO,
	max_value=DeviceParamConstantType.MAX_FREQUENCY,
	min_value=DeviceParamConstantType.MIN_FREQUENCY,
)

field_frequency = AnswerFieldDef(
    field_name=EFieldName.FREQUENCY,
    field_type=field_type_frequency,
)

field_type_gain = FieldType(
    field_type=np.uint8,
    si_unit=SIUnit.PERCENT,
    si_prefix=SIPrefix.NONE,
	max_value=DeviceParamConstantType.MAX_GAIN,
	min_value=DeviceParamConstantType.MIN_GAIN,
)

field_gain = AnswerFieldDef(
    field_name=EFieldName.GAIN,
    field_type=field_type_gain
)

field_signal = AnswerFieldDef(
    field_name=EFieldName.SIGNAL,
    field_type=FieldType(field_type=bool, converter_ref=ConverterType.SIGNAL),
)

field_procedure = AnswerFieldDef(
    field_name=EFieldName.PROCEDURE,
    field_type=FieldType(field_type=Procedure, converter_ref=ConverterType.ENUM),
)

swf_field_type = FieldType(
    field_type=np.uint8,
    si_unit=SIUnit.HERTZ,
    #si_prefix=SIPrefix.KILO,
	max_value=DeviceParamConstantType.MAX_SWF,
	min_value=DeviceParamConstantType.MIN_SWF,
)

field_swf = AnswerFieldDef(
    field_name=EFieldName.SWF,
    field_type=swf_field_type
)

field_type_temperature_kelvin = FieldType(
    field_type=np.uint32,
    si_unit=SIUnit.KELVIN,
    si_prefix=SIPrefix.MILLI,
)

field_type_temperature_celsius = FieldType(
    field_type=float,
    si_unit=SIUnit.CELSIUS,
    si_prefix=SIPrefix.NONE,
)

field_temperature_kelvin = AnswerFieldDef(
    field_name=EFieldName.TEMPERATURE,
    field_type=field_type_temperature_kelvin
)

field_temperature_celsius = AnswerFieldDef(
    field_name=EFieldName.TEMPERATURE,
    field_type=field_type_temperature_celsius
)

urms_field_type = FieldType(
    field_type=np.uint32,
    si_unit=SIUnit.VOLTAGE,
    si_prefix=SIPrefix.MICRO,
)

irms_field_type = FieldType(
    field_type=np.uint32,
    si_unit=SIUnit.AMPERE,
    si_prefix=SIPrefix.MICRO,
)

phase_field_type = FieldType(
    field_type=np.uint32,
    si_unit=SIUnit.DEGREE,
    si_prefix=SIPrefix.MICRO,
)

ts_flag_field_type = FieldType(
    field_type=np.uint32,
    si_unit=SIUnit.VOLTAGE,
    si_prefix=SIPrefix.MICRO,
)

field_urms = AnswerFieldDef(
    field_name=EFieldName.URMS,
    field_type=urms_field_type
)

field_irms = AnswerFieldDef(
    field_name=EFieldName.IRMS,
    field_type=irms_field_type
)

field_phase = AnswerFieldDef(
    field_name=EFieldName.PHASE,
    field_type=phase_field_type
)

field_ts_flag = AnswerFieldDef(
    field_name=EFieldName.TS_FLAG,
    field_type=ts_flag_field_type
)

field_unknown_answer = AnswerFieldDef(
	field_name=EFieldName.UNKNOWN_ANSWER,
	field_type=FieldType(str)
)

field_type_time_span = FieldType(
    field_type=np.uint32,
    min_value=np.uint32(0),
    si_unit=SIUnit.SECONDS,
    si_prefix=SIPrefix.MILLI
)

field_scan_f_step = AnswerFieldDef(
    field_name=EFieldName.SCAN_F_STEP,
    field_type=field_type_frequency,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Scst: ")
)

field_scan_f_half_range = AnswerFieldDef(
    field_name=EFieldName.SCAN_F_RANGE,
    field_type=field_type_frequency,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Range: ")
)

field_scan_t_step = AnswerFieldDef(
    field_name=EFieldName.SCAN_T_STEP,
    field_type=field_type_time_span,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Ton: ")
)

field_tune_f_step = AnswerFieldDef(
    field_name=EFieldName.TUNE_F_STEP,
    field_type=field_type_frequency,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Tust: ")
)

field_tune_t_time = AnswerFieldDef(
    field_name=EFieldName.TUNE_T_TIME,
    field_type=field_type_time_span,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Tust: ")
)

field_wipe_f_step = AnswerFieldDef(
    field_name=EFieldName.WIPE_F_STEP,
    field_type=field_type_frequency,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Step: ")
)

field_wipe_f_range = AnswerFieldDef(
    field_name=EFieldName.WIPE_F_RANGE,
    field_type=field_type_frequency,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Range: ")
)

field_wipe_t_on = AnswerFieldDef(
    field_name=EFieldName.WIPE_T_ON,
    field_type=field_type_time_span,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Ton: ")
)

field_wipe_t_off = AnswerFieldDef(
    field_name=EFieldName.WIPE_T_OFF,
    field_type=field_type_time_span,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Toff: ")
)

field_wipe_t_pause = AnswerFieldDef(
    field_name=EFieldName.WIPE_T_PAUSE,
    field_type=field_type_time_span,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Pause: ")
)

field_duty_cycle_t_on = AnswerFieldDef(
    field_name=EFieldName.DUTY_CYCLE_T_ON,
    field_type=field_type_time_span,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Ton: ")
)

field_duty_cycle_t_off = AnswerFieldDef(
    field_name=EFieldName.DUTY_CYCLE_T_OFF,
    field_type=field_type_time_span,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Toff: ")
)
