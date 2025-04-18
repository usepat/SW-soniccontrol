from typing import List
import numpy as np
from sonic_protocol.command_contracts.contract_generators import create_list_with_unknown_answer_alternative, create_version_field
from sonic_protocol.protocol import (build_date_field, build_hash_field, field_device_type)
from sonic_protocol.defs import (
    CommandCode, CommandExport, CommandListExport, CommandParamDef, ConverterType, DeviceParamConstants, FieldType, MetaExport, MetaExportDescriptor, Procedure, 
    Protocol, SonicTextCommandAttrs, UserManualAttrs, Version, CommandDef, AnswerDef,
    AnswerFieldDef, CommandContract, DeviceType,
)
from sonic_protocol.command_contracts.fields import (
    field_frequency, field_gain, field_temperature_kelvin, field_urms, field_irms, 
    field_phase, field_signal, field_type_frequency, field_type_gain,
)


from sonic_protocol.field_names import EFieldName


# Version instance
version = Version(major=0, minor=0, patch=0)




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



dash = CommandContract(
            code=CommandCode.GET_UPDATE,
            command_defs=CommandDef(
                sonic_text_attrs=SonicTextCommandAttrs(
                    string_identifier=["-"]
                )
            ),
            answer_defs=AnswerDef(
                fields=[
                    #error_code_field,
                    field_frequency,
                    field_gain,
                    #procedure_field,
                    field_temperature_kelvin,
                    field_urms,
                    field_irms,
                    field_phase,
                    field_signal,
                ]
            ),
            user_manual_attrs=UserManualAttrs(
                description="Mainly used by sonic control to get a short and computer friendly parsable status update."
            ),
            is_release=True,
            tags=["update", "status"]
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

param_frequency = CommandParamDef(
    name=EFieldName.FREQUENCY,
    param_type=field_type_frequency,
    user_manual_attrs=UserManualAttrs(
        description="Frequency of the transducer"
    )
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


legacy_protocol = Protocol(
    version=Version(0, 0, 0),
    consts=DeviceParamConstants(),
    commands=[
        CommandListExport(
            exports=[
                        get_info, 
                        dash,
                        set_on,
                        set_off,
                        set_frequency,
                        set_gain,
                    ],
            descriptor=MetaExportDescriptor(min_protocol_version=version)
        )
         # freq
        # gain
        # temp
        # tpcb
        # sens
        # prot
        # list
        # pval
        # exD0
        # exD1
        # ?duty
        #  ?
        # -
        # =
        # !KHZ
        # !MHZ
        # !ON
        # !OFF
        # !WIPE
        # !AUTO
        # !SERIAL
        # """ 
    ]

)
