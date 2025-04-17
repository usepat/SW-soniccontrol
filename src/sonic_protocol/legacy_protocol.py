from typing import List
import numpy as np
from sonic_protocol.command_contracts.contract_generators import create_version_field
from sonic_protocol.protocol import (build_date_field, build_hash_field, field_device_type)
from sonic_protocol.defs import (
    CommandCode, CommandExport, CommandListExport, ConverterType, DeviceParamConstants, FieldType, MetaExport, MetaExportDescriptor, Procedure, 
    Protocol, SonicTextCommandAttrs, UserManualAttrs, Version, CommandDef, AnswerDef,
    AnswerFieldDef, CommandContract, DeviceType,
)
from sonic_protocol.command_contracts.fields import (
    field_frequency, field_gain, field_temperature_kelvin, field_urms, field_irms, 
    field_phase, field_signal
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
                    error_code_field,
                    field_frequency,
                    field_gain,
                    procedure_field,
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

get_type = CommandContract(
    code=None,
    command_defs=None,
    answer_defs=None,
    is_release=True,
    tags=[" "]
    user_manual_attrs=UserManualAttrs(
        description=""
    ),
)

get_freq = CommandContract(
    code=None,
    command_defs=None,
    answer_defs=None,
    is_release=True,
    tags=[" "]
    user_manual_attrs=UserManualAttrs(
        description=""
    ),
)

get_gain = CommandContract(
    code=None,
    command_defs=None,
    answer_defs=None,
    is_release=True,
    tags=[" "]
    user_manual_attrs=UserManualAttrs(
        description=""
    ),
)

get_temp = CommandContract(
    code=None,
    command_defs=None,
    answer_defs=None,
    is_release=True,
    tags=[" "]
    user_manual_attrs=UserManualAttrs(
        description=""
    ),
)

get_type = CommandContract(
    code=None,
    command_defs=None,
    answer_defs=None,
    is_release=True,
    tags=[" "]
    user_manual_attrs=UserManualAttrs(
        description=""
    ),
)

get_type = CommandContract(
    code=None,
    command_defs=None,
    answer_defs=None,
    is_release=True,
    tags=[" "]
    user_manual_attrs=UserManualAttrs(
        description=""
    ),
)

get_type = CommandContract(
    code=None,
    command_defs=None,
    answer_defs=None,
    is_release=True,
    tags=[" "]
    user_manual_attrs=UserManualAttrs(
        description=""
    ),
)

get_type = CommandContract(
    code=None,
    command_defs=None,
    answer_defs=None,
    is_release=True,
    tags=[" "]
    user_manual_attrs=UserManualAttrs(
        description=""
    ),
)

get_type = CommandContract(
    code=None,
    command_defs=None,
    answer_defs=None,
    is_release=True,
    tags=[" "]
    user_manual_attrs=UserManualAttrs(
        description=""
    ),
)

legacy_protocol = Protocol(
    version=Version(0, 0, 0),
    consts=DeviceParamConstants(),
    commands=[
        CommandListExport(
            exports=[get_info, dash],
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
