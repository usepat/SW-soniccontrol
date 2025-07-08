import numpy as np
from sonic_protocol.schema import (
    Procedure, DeviceParamConstantType, FieldType, AnswerFieldDef, ConverterType, SIPrefix, SIUnit, 
    SonicTextAnswerFieldAttrs
)
from sonic_protocol.protocols.protocol_v1_0_0.transducer_commands.transducer_fields import (
    field_type_frequency, field_type_gain, field_type_frequency_step
)
from sonic_protocol.field_names import EFieldName

field_procedure = AnswerFieldDef(
    field_name=EFieldName.PROCEDURE,
    field_type=FieldType(field_type=Procedure, converter_ref=ConverterType.ENUM),
)

field_type_time_span_off = FieldType(
    field_type=np.uint32,
    min_value=DeviceParamConstantType.MIN_T_OFF,
    max_value=DeviceParamConstantType.MAX_T_OFF,
    si_unit=SIUnit.SECONDS,
    si_prefix=SIPrefix.MILLI
)

field_type_time_span_on = FieldType(
    field_type=np.uint32,
    min_value=DeviceParamConstantType.MIN_T_ON,
    max_value=DeviceParamConstantType.MAX_T_ON,
    si_unit=SIUnit.SECONDS,
    si_prefix=SIPrefix.MILLI
)

field_type_f_shift = FieldType(
    field_type=np.uint32,
    min_value=DeviceParamConstantType.MIN_F_SHIFT,
    max_value=DeviceParamConstantType.MAX_F_SHIFT,
    si_unit=SIUnit.HERTZ
)

field_type_n_steps = FieldType(
    field_type=np.uint8,
    min_value=DeviceParamConstantType.MIN_N_STEPS
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

field_ramp_f_step = AnswerFieldDef(
    field_name=EFieldName.RAMP_F_STEP,
    field_type=field_type_frequency_step,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Step: ")
)

field_ramp_t_off = AnswerFieldDef(
    field_name=EFieldName.RAMP_T_OFF,
    field_type=field_type_time_span_off,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Toff: ")
)

field_ramp_t_on = AnswerFieldDef(
    field_name=EFieldName.RAMP_T_ON,
    field_type=field_type_time_span_on,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Ton: ")
)

field_scan_f_step = AnswerFieldDef(
    field_name=EFieldName.SCAN_F_STEP,
    field_type=field_type_frequency_step,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Scst: ")
)

field_scan_f_half_range = AnswerFieldDef(
    field_name=EFieldName.SCAN_F_RANGE,
    field_type=field_type_frequency_step,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Range: ")
)

field_scan_f_shift = AnswerFieldDef(
    field_name=EFieldName.SCAN_F_SHIFT,
    field_type=field_type_f_shift,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Fshift: ")
)

field_scan_t_step = AnswerFieldDef(
    field_name=EFieldName.SCAN_T_STEP,
    field_type=field_type_time_span_on,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Ton: ")
)

field_scan_gain = AnswerFieldDef(
    field_name=EFieldName.SCAN_GAIN,
    field_type=field_type_gain,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Gain: ")
)

field_tune_f_step = AnswerFieldDef(
    field_name=EFieldName.TUNE_F_STEP,
    field_type=field_type_frequency_step,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Tust: ")
)

field_tune_f_shift = AnswerFieldDef(
    field_name=EFieldName.TUNE_F_SHIFT,
    field_type=field_type_f_shift,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Fshift: ")
)

field_tune_t_step = AnswerFieldDef(
    field_name=EFieldName.TUNE_T_STEP,
    field_type=field_type_time_span_on,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Tstep: ")
)

field_tune_t_time = AnswerFieldDef(
    field_name=EFieldName.TUNE_T_TIME,
    field_type=field_type_time_span_on,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Tutm: ")
)

field_tune_n_steps = AnswerFieldDef(
    field_name=EFieldName.TUNE_N_STEPS,
    field_type=field_type_n_steps,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Nsteps: ")
)

field_tune_gain = AnswerFieldDef(
    field_name=EFieldName.TUNE_GAIN,
    field_type=field_type_gain,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Gain: ")
)

field_wipe_f_step = AnswerFieldDef(
    field_name=EFieldName.WIPE_F_STEP,
    field_type=field_type_frequency_step,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Step: ")
)

field_wipe_f_range = AnswerFieldDef(
    field_name=EFieldName.WIPE_F_RANGE,
    field_type=field_type_frequency_step,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Range: ")
)

field_wipe_t_on = AnswerFieldDef(
    field_name=EFieldName.WIPE_T_ON,
    field_type=field_type_time_span_on,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Ton: ")
)

field_wipe_t_off = AnswerFieldDef(
    field_name=EFieldName.WIPE_T_OFF,
    field_type=field_type_time_span_off,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Toff: ")
)

field_wipe_t_pause = AnswerFieldDef(
    field_name=EFieldName.WIPE_T_PAUSE,
    field_type=field_type_time_span_off,
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Pause: ")
)

field_duty_cycle_t_on = AnswerFieldDef(
    field_name=EFieldName.DUTY_CYCLE_T_ON,
    field_type= FieldType(
        field_type=np.uint32,
        min_value=DeviceParamConstantType.MIN_DUTY_CYCLE_T_ON,
        max_value=DeviceParamConstantType.MAX_DUTY_CYCLE_T_ON,
        si_unit=SIUnit.SECONDS,
    ),
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Ton: "),
)

field_duty_cycle_t_off = AnswerFieldDef(
    field_name=EFieldName.DUTY_CYCLE_T_OFF,
    field_type=FieldType(
        field_type=np.uint32,
        min_value=DeviceParamConstantType.MIN_DUTY_CYCLE_T_OFF,
        max_value=DeviceParamConstantType.MAX_DUTY_CYCLE_T_OFF,
        si_unit=SIUnit.SECONDS,
    ),
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Toff: ")
)