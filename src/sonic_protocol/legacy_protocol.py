from typing import List
import numpy as np
from sonic_protocol.command_contracts.contract_generators import create_list_with_unknown_answer_alternative, create_version_field
from sonic_protocol.protocol import (build_date_field, build_hash_field, field_device_type)
from sonic_protocol.defs import (
    CommandCode, CommandExport, CommandListExport, CommandParamDef, ConverterType, DeviceParamConstantType, DeviceParamConstants, FieldType, MetaExport, MetaExportDescriptor, Procedure, 
    Protocol, SIPrefix, SIUnit, SonicTextCommandAttrs, UserManualAttrs, Version, CommandDef, AnswerDef,
    AnswerFieldDef, CommandContract, DeviceType,
)
# from sonic_protocol.command_contracts.fields import (

# )


from sonic_protocol.field_names import EFieldName


# Version instance
version = Version(major=1, minor=0, patch=0)




get_info = CommandContract(
    code=CommandCode.GET_INFO,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier="?info"
        )
    ),
    answer_defs=AnswerDef(
        fields=[
            field_device_type,
            create_version_field(EFieldName.HARDWARE_VERSION),
            create_version_field(EFieldName.FIRMWARE_VERSION),
            build_hash_field,
            build_date_field,
        ]
    ),
    is_release=True
)






field_unknown_answer = AnswerFieldDef(
	field_name=EFieldName.UNKNOWN_ANSWER,
	field_type=FieldType(str)
)

set_on = CommandContract(
    code=CommandCode.SET_ON,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!ON"]
        )
    ),
    answer_defs=AnswerDef(fields=[field_unknown_answer]),
    is_release=True,
    tags=[" "],
    user_manual_attrs=UserManualAttrs(
        description=""
    ),
)


set_off = CommandContract(
    code=CommandCode.SET_OFF,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!OFF"]
        )
    ),
    answer_defs=AnswerDef(fields=[field_unknown_answer]),
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
    command_defs=CommandDef(
        index_param=None,
        setter_param=param_frequency,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!f"]
        )
    ),
    answer_defs=create_list_with_unknown_answer_alternative(
        AnswerDef(fields=[field_frequency])
    ),
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
    command_defs=CommandDef(
        index_param=None,
        setter_param=param_gain,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!g", "!gain", "set_gain"]
        )
    ),
    answer_defs=create_list_with_unknown_answer_alternative(
        AnswerDef(fields=[field_gain])
    ),
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
    field_name=EFieldName.RANG,
    field_type=FieldType(
        field_type=np.uint32,
    )
)

field_step = AnswerFieldDef(
    field_name=EFieldName.STEP,
    field_type=FieldType(
        field_type=np.uint32,
    )
)

field_sing = AnswerFieldDef(
    field_name=EFieldName.SING,
    field_type=FieldType(
        field_type=np.uint32,
    )
)

field_paus = AnswerFieldDef(
    field_name=EFieldName.PAUS,
    field_type=FieldType(
        field_type=np.uint32,
    )
)

get_pval = CommandContract(
    code=CommandCode.GET_PVAL,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?pval"]
        )
    ),
    answer_defs=AnswerDef(
        fields=[
            field_rang,
            field_step,
            field_sing,
            field_paus,
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to get the pval of the transducer on the device."
    ),
    is_release=True
)

dash = CommandContract(
            code=CommandCode.GET_UPDATE,
            command_defs=CommandDef(
                sonic_text_attrs=SonicTextCommandAttrs(
                    string_identifier=["-"]
                )
            ),
            answer_defs=AnswerDef(
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


class LegacyProtocol(Protocol):
    # TODO Fix this and INFO tab
    @property
    def major_version(self) -> int:
        return 2

legacy_protocol = LegacyProtocol(
    version=Version(1, 0, 0),
    consts=DeviceParamConstants(
        min_frequency=600000,
        max_frequency=6000000,
    ),
    commands=[
        CommandListExport(
            exports=[
                        get_info, 
                        dash,
                        set_on,
                        set_off,
                        set_frequency,
                        set_gain,
                        get_pval,
                    ],
            descriptor=MetaExportDescriptor(min_protocol_version=version)
        )
    ]
)
