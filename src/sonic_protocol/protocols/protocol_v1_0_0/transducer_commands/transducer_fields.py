import numpy as np
from sonic_protocol.defs import CommandParamDef, Procedure, DeviceParamConstantType, DeviceType, FieldType, AnswerFieldDef, CommunicationChannel, ConverterType, SIPrefix, SIUnit, SonicTextAnswerFieldAttrs, UserManualAttrs, Version, Waveform
from sonic_protocol.field_names import EFieldName


field_type_frequency = FieldType(
    field_type=np.uint32,
    si_unit=SIUnit.HERTZ,
    #si_prefix=SIPrefix.KILO,
	max_value=DeviceParamConstantType.MAX_FREQUENCY,
	min_value=DeviceParamConstantType.MIN_FREQUENCY,
)

field_type_atf = FieldType(
    field_type=np.uint32,
    si_unit=SIUnit.HERTZ,
    #si_prefix=SIPrefix.KILO,
	max_value=DeviceParamConstantType.MAX_FREQUENCY,
	min_value=DeviceParamConstantType.MIN_FREQUENCY,
    allowed_values=(np.uint32(0),)
)

field_type_frequency_step = FieldType(
    field_type=np.uint32,
    si_unit=SIUnit.HERTZ,
    #si_prefix=SIPrefix.KILO,
	max_value=DeviceParamConstantType.MAX_F_STEP,
	min_value=DeviceParamConstantType.MIN_F_STEP,
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
    min_value=np.uint32(0),
    max_value=np.uint32(6273150), # The sun is 6000 °C warm. max limit is that converted into kelvin
    si_unit=SIUnit.KELVIN,
    si_prefix=SIPrefix.MILLI,
)

field_type_temperature_celsius = FieldType(
    field_type=float,
    min_value=-273.15, # Absolute zero point
    max_value=6000., # The sun is 6000 °C warm.
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
waveform_field_type = FieldType(
    field_type=Waveform,
    converter_ref=ConverterType.ENUM
)
field_waveform = AnswerFieldDef(
    field_name=EFieldName.WAVEFORM,
    field_type=waveform_field_type
)

field_phase = AnswerFieldDef(
    field_name=EFieldName.PHASE,
    field_type=phase_field_type
)

field_ts_flag = AnswerFieldDef(
    field_name=EFieldName.TS_FLAG,
    field_type=ts_flag_field_type
)

field_transducer = AnswerFieldDef(
    field_name=EFieldName.TRANSDUCER_ID,
    field_type=FieldType(str)
)

param_frequency = CommandParamDef(
    name=EFieldName.FREQUENCY,
    param_type=field_type_frequency,
    user_manual_attrs=UserManualAttrs(
        description="Frequency of the transducer"
    )
)

param_gain = CommandParamDef(
    name=EFieldName.GAIN,
    param_type=field_type_gain,
    user_manual_attrs=UserManualAttrs(
        description="Gain of the transducer"
    )
)

param_swf = CommandParamDef(
    name=EFieldName.SWF,
    param_type=swf_field_type,
    user_manual_attrs=UserManualAttrs(
        description="Switching frequency of the transducer"
    )
)


param_index = CommandParamDef(
    name=EFieldName.INDEX,
    param_type=FieldType(
        field_type=np.uint8,
        min_value=DeviceParamConstantType.MIN_TRANSDUCER_INDEX,
        max_value=DeviceParamConstantType.MAX_TRANSDUCER_INDEX,
    )
)
param_atf = CommandParamDef(
    name=EFieldName.ATF,
    param_type=field_type_atf
)

param_att = CommandParamDef(
    name=EFieldName.ATT,
    param_type=field_type_temperature_celsius
)

field_type_atk = FieldType(
    float,
    min_value=-10000000,
    max_value=+10000000
)

param_atk = CommandParamDef(
    name=EFieldName.ATK,
    param_type=field_type_atk
)

field_atf = AnswerFieldDef(
    field_name=EFieldName.ATF,
    field_type=field_type_atf
)

field_att = AnswerFieldDef(
    field_name=EFieldName.ATT,
    field_type=field_type_temperature_celsius
)

field_atk = AnswerFieldDef(
    field_name=EFieldName.ATK,
    field_type=field_type_atk
)

param_waveform = CommandParamDef(
    name=EFieldName.WAVEFORM,
    param_type=waveform_field_type
)

param_temp_celsius = CommandParamDef(
    name=EFieldName.TEMPERATURE,
    param_type=field_type_temperature_celsius,
    user_manual_attrs=UserManualAttrs(
        description="Temperature of the device in celsius"
    )
)