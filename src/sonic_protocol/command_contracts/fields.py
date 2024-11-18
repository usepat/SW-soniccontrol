from sonic_protocol.defs import Procedure, DeviceParamConstantType, DeviceType, FieldType, AnswerFieldDef, CommunicationChannel, ConverterType, SIPrefix, SIUnit, Version
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
    field_type=int,
    si_unit=SIUnit.HERTZ,
    si_prefix=SIPrefix.KILO,
	max_value=DeviceParamConstantType.MAX_FREQUENCY,
	min_value=DeviceParamConstantType.MIN_FREQUENCY,
)

field_frequency = AnswerFieldDef(
    field_name=EFieldName.FREQUENCY,
    field_type=field_type_frequency,
)

field_type_gain = FieldType(
    field_type=int,
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
    field_type=int,
    si_unit=SIUnit.HERTZ,
    si_prefix=SIPrefix.KILO,
	max_value=DeviceParamConstantType.MAX_SWF,
	min_value=DeviceParamConstantType.MIN_SWF,
)

field_swf = AnswerFieldDef(
    field_name=EFieldName.SWF,
    field_type=swf_field_type
)

field_type_temperature = FieldType(
    field_type=int,
    si_unit=SIUnit.CELSIUS,
    si_prefix=SIPrefix.NONE,
)

field_temperature = AnswerFieldDef(
    field_name=EFieldName.TEMPERATURE,
    field_type=field_type_temperature
)

urms_field_type = FieldType(
    field_type=int,
    si_unit=SIUnit.VOLTAGE,
    si_prefix=SIPrefix.MICRO,
)

irms_field_type = FieldType(
    field_type=int,
    si_unit=SIUnit.AMPERE,
    si_prefix=SIPrefix.MICRO,
)

phase_field_type = FieldType(
    field_type=int,
    si_unit=SIUnit.DEGREE,
    si_prefix=SIPrefix.MICRO,
)

ts_flag_field_type = FieldType(
    field_type=int,
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
