from typing import List
import numpy as np
from sonic_protocol.command_contracts.contract_generators import create_version_field
from sonic_protocol.defs import (
    CommandCode, CommandParamDef, DeviceParamConstantType, FieldType,
    SIPrefix, SIUnit, SonicTextAnswerFieldAttrs, SonicTextCommandAttrs, UserManualAttrs, Version, CommandDef, AnswerDef,
    AnswerFieldDef, CommandContract, SonicTextAnswerAttrs
)
# from sonic_protocol.command_contracts.fields import (

# )


from sonic_protocol.field_names import EFieldName


# Version instance
version = Version(major=1, minor=0, patch=0)


field_unknown_answer = AnswerFieldDef(
	field_name=EFieldName.UNKNOWN_ANSWER,
	field_type=FieldType(str)
)

set_on = CommandContract(
    code=CommandCode.SET_ON,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!ON"]
        )
    ),
    answer_def=AnswerDef(fields=[field_unknown_answer]),
    is_release=True,
    tags=[" "],
    user_manual_attrs=UserManualAttrs(
        description=""
    ),
)

set_auto = CommandContract(
    code=CommandCode.LEGACY_AUTO,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!AUTO"]
        )
    ),
    answer_def=AnswerDef(fields=[field_unknown_answer]),
    is_release=True,
    tags=[" "],
    user_manual_attrs=UserManualAttrs(
        description=""
    ),
)

set_wipe = CommandContract(
    code=CommandCode.LEGACY_WIPE,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!WIPE"]
        )
    ),
    answer_def=AnswerDef(fields=[field_unknown_answer]),
    is_release=True,
    tags=[" "],
    user_manual_attrs=UserManualAttrs(
        description=""
    ),
)


set_off = CommandContract(
    code=CommandCode.SET_OFF,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!OFF"]
        )
    ),
    answer_def=AnswerDef(fields=[field_unknown_answer]),
    is_release=True,
    tags=[" "],
    user_manual_attrs=UserManualAttrs(
        description=""
    ),
)
field_type_gain = FieldType(
    field_type=np.uint8,
	max_value=DeviceParamConstantType.MAX_GAIN,
	min_value=DeviceParamConstantType.MIN_GAIN,
    )

field_type_frequency = FieldType(
    field_type=np.uint32,
    si_unit=SIUnit.HERTZ,
    si_prefix=SIPrefix.NONE,
	max_value=DeviceParamConstantType.MAX_FREQUENCY,
	min_value=DeviceParamConstantType.MIN_FREQUENCY,
    )

param_frequency = CommandParamDef(
    name=EFieldName.FREQUENCY,
    param_type=field_type_frequency,
    user_manual_attrs=UserManualAttrs(
        description="Frequency of the transducer"
    )
)
field_gain = AnswerFieldDef(
    field_name=EFieldName.GAIN,
    field_type=field_type_gain
)
field_frequency = AnswerFieldDef(
    field_name=EFieldName.FREQUENCY,
    field_type=field_type_frequency
)

set_frequency = CommandContract(
    code=CommandCode.SET_FREQ,
    command_def=CommandDef(
        index_param=None,
        setter_param=param_frequency,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!f"]
        )
    ),
    answer_def=AnswerDef(fields=[field_frequency]),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the frequency of the transducer on the device."
    ),
    is_release=True,
    tags=["frequency", "transducer"]
)


param_gain = CommandParamDef(
    name=EFieldName.GAIN,
    param_type=field_type_gain,
    user_manual_attrs=UserManualAttrs(
        description="Gain of the transducer"
    )
)


set_gain = CommandContract(
    code=CommandCode.SET_GAIN,
    command_def=CommandDef(
        index_param=None,
        setter_param=param_gain,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!g", "!gain", "set_gain"]
        )
    ),
    answer_def=AnswerDef(fields=[field_gain]),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the gain of the transducer on the device."
    ),
    is_release=True,
    tags=["gain", "transducer"],
)

field_error_code = AnswerFieldDef(
    field_name=EFieldName.ERROR_CODE,
    field_type=FieldType(
        field_type=np.uint8,
    )
)

field_frequency_no_unit = AnswerFieldDef(
    field_name=EFieldName.FREQUENCY,
    field_type=FieldType(
        field_type=np.uint32,
    )
)

field_procedure = AnswerFieldDef(
    field_name=EFieldName.UNDEFINED,
    field_type=FieldType(
        field_type=str,
    )
)

field_signal = AnswerFieldDef(
    field_name=EFieldName.SIGNAL,
    field_type=FieldType(
        field_type=bool,
    )
)

field_temperature = AnswerFieldDef(
    field_name=EFieldName.TEMPERATURE,
    field_type=FieldType(
        field_type=float,
    )
)

field_urms = AnswerFieldDef(
    field_name=EFieldName.URMS,
    field_type=FieldType(
        field_type=np.uint32,
    )
)

field_irms = AnswerFieldDef(
    field_name=EFieldName.IRMS,
    field_type=FieldType(
        field_type=np.uint32,
    )
)

field_phase = AnswerFieldDef(
    field_name=EFieldName.PHASE,
    field_type=FieldType(
        field_type=np.uint32,
    )
)

field_rang = AnswerFieldDef(
    field_name=EFieldName.LEGACY_RANG,
    field_type=FieldType(
        field_type=np.uint32,
    )
)

field_step = AnswerFieldDef(
    field_name=EFieldName.LEGACY_STEP,
    field_type=FieldType(
        field_type=np.uint32,
    )
)

field_sing = AnswerFieldDef(
    field_name=EFieldName.LEGACY_SING,
    field_type=FieldType(
        field_type=np.uint32,
    )
)

field_paus = AnswerFieldDef(
    field_name=EFieldName.LEGACY_PAUS,
    field_type=FieldType(
        field_type=np.uint32,
    )
)

uint32_param = CommandParamDef(
            name=EFieldName.UNDEFINED,
            param_type=FieldType(
                field_type=np.uint32,
            )
        )

set_step = CommandContract(
    code=CommandCode.LEGACY_STEP,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!step"]
        ),
        setter_param=uint32_param
    ),
    answer_def=AnswerDef(
        fields=[
            field_step
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the frequency step size for the wipe procedure."
    ),
    is_release=True
)

set_sing = CommandContract(
    code=CommandCode.LEGACY_SING,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!sing"]
        ),
        setter_param=uint32_param
    ),
    answer_def=AnswerDef(
        fields=[
            field_sing
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the sing parameter for the wipe procedure."
    ),
    is_release=True
)

set_paus = CommandContract(
    code=CommandCode.LEGACY_PAUS,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!paus"]
        ),
        setter_param=uint32_param
    ),
    answer_def=AnswerDef(
        fields=[
            field_paus
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the paus parameter for the wipe procedure."
    ),
    is_release=True
)

set_rang = CommandContract(
    code=CommandCode.LEGACY_RANG,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!rang"]
        ),
        setter_param=uint32_param
    ),
    answer_def=AnswerDef(
        fields=[
            field_rang
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the rang parameter for the wipe procedure."
    ),
    is_release=True
)

field_rang_pval = AnswerFieldDef(
    field_name=EFieldName.LEGACY_RANG,
    field_type=FieldType(
        field_type=np.uint32,
    ),
    sonic_text_attrs=SonicTextAnswerFieldAttrs(
        prefix="rang:"
    )
)

field_step_pval = AnswerFieldDef(
    field_name=EFieldName.LEGACY_STEP,
    field_type=FieldType(
        field_type=np.uint32,
    ),
    sonic_text_attrs=SonicTextAnswerFieldAttrs(
        prefix="step:"
    )
)

field_sing_pval = AnswerFieldDef(
    field_name=EFieldName.LEGACY_SING,
    field_type=FieldType(
        field_type=np.uint32,
    ),
    sonic_text_attrs=SonicTextAnswerFieldAttrs(
        prefix="sing:"
    )
)

field_paus_pval = AnswerFieldDef(
    field_name=EFieldName.LEGACY_PAUS,
    field_type=FieldType(
        field_type=np.uint32,
    ),
    sonic_text_attrs=SonicTextAnswerFieldAttrs(
        prefix="paus:"
    )
)

get_pval = CommandContract(
    code=CommandCode.LEGACY_PVAL,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?pval"]
        )
    ),
    answer_def=AnswerDef(
        fields=[
            field_rang_pval,
            field_step_pval,
            field_sing_pval,
            field_paus_pval,
        ],
        sonic_text_attrs=SonicTextAnswerAttrs(
            separator="\r\n"
        )
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to get the pval of the transducer on the device."
    ),
    is_release=True
)

field_tust = AnswerFieldDef(
    field_name=EFieldName.LEGACY_TUST,
    field_type=FieldType(
        field_type=np.uint32,
    )
)

field_tutm = AnswerFieldDef(
    field_name=EFieldName.LEGACY_TUTM,
    field_type=FieldType(
        field_type=np.uint32,
    )
)

field_scst = AnswerFieldDef(
    field_name=EFieldName.LEGACY_SCST,
    field_type=FieldType(
        field_type=np.uint32,
    )
)

set_tust = CommandContract(
    code=CommandCode.LEGACY_TUST,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!tust"]
        ),
        setter_param=uint32_param
    ),
    answer_def=AnswerDef(
        fields=[
            field_tust
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the tune steps for the auto procedure."
    ),
    is_release=True
)



set_tutm = CommandContract(
    code=CommandCode.LEGACY_TUTM,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!tutm"]
        ),
        setter_param=uint32_param
    ),
    answer_def=AnswerDef(
        fields=[
            field_tutm
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the tune time for the auto procedure."
    ),
    is_release=True
)

set_scst = CommandContract(
    code=CommandCode.LEGACY_SCST,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!scst"]
        ),
        setter_param=uint32_param
    ),
    answer_def=AnswerDef(
        fields=[
            field_scst
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the scanning for the auto procedure."
    ),
    is_release=True
)


dash = CommandContract(
            code=CommandCode.GET_UPDATE,
            command_def=CommandDef(
                sonic_text_attrs=SonicTextCommandAttrs(
                    string_identifier=["-"]
                )
            ),
            answer_def=AnswerDef(
                fields=[
                    field_error_code,
                    field_frequency_no_unit,
                    field_gain,
                    field_procedure,
                    field_signal,
                    field_temperature,
                    field_urms,
                    field_irms,
                    field_phase,
                ]
            ),
            user_manual_attrs=UserManualAttrs(
                description="Mainly used by sonic control to get a short and computer friendly parsable status update."
            ),
            is_release=True,
            tags=["update", "status"]
        )

param_index = CommandParamDef(
    name=EFieldName.INDEX,
    param_type=FieldType(
        field_type=np.uint8,
        min_value=DeviceParamConstantType.MIN_TRANSDUCER_INDEX,
        max_value=DeviceParamConstantType.MAX_TRANSDUCER_INDEX,
    )
)

float_param = FieldType(
    field_type=float,
)

param_atf = CommandParamDef(
    name=EFieldName.ATF,
    param_type=uint32_param
)

param_att = CommandParamDef(
    name=EFieldName.ATT,
    param_type=float_param
)

uint32_field = FieldType(
    field_type=np.uint32
)

float_field = FieldType(
    field_type=float
)

param_atk = CommandParamDef(
    name=EFieldName.ATK,
    param_type=uint32_field
)

field_atf = AnswerFieldDef(
    field_name=EFieldName.ATF,
    field_type=float_field
)

set_atf = CommandContract(
    code=CommandCode.SET_ATF,
    command_def=CommandDef(
        index_param=param_index,
        setter_param=param_atf,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!atf"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_atf]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the atf"
    ),
    is_release=True,
    tags=["transducer", "config"]
)

field_att = AnswerFieldDef(
    field_name=EFieldName.ATT,
    field_type=float_field
)


set_att = CommandContract(
    code=CommandCode.SET_ATT,
    command_def=CommandDef(
        index_param=param_index,
        setter_param=param_att, # TODO make a better param for att
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!att"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_att]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the att"
    ),
    is_release=True,
    tags=["transducer", "config"]
)

field_atk = AnswerFieldDef(
    field_name=EFieldName.ATK,
    field_type=float_field
)


set_atk = CommandContract(
    code=CommandCode.SET_ATK,
    command_def=CommandDef(
        index_param=param_index,
        setter_param=param_atk,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!atk"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_atk]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the atk"
    ),
    is_release=True,
    tags=["transducer", "config"]
)

crystal_commands = [ 
    dash,
    set_on,
    set_off,
    set_frequency,
    set_gain,
    get_pval,
    set_paus,
    set_sing,
    set_step,
    set_rang,
    set_tust,
    set_tutm,
    set_scst,
    set_auto,
    set_wipe,
    set_atf,
    set_atk,
    set_att
]

crystal_constants = {
    DeviceParamConstantType.MIN_FREQUENCY: 600000,
    DeviceParamConstantType.MAX_FREQUENCY: 6000000,
}
