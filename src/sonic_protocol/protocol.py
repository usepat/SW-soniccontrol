from typing import List
import numpy as np
from sonic_protocol.command_contracts.contract_generators import create_version_field
from sonic_protocol.defs import (
    CommandCode, CommandExport, CommandListExport, ConverterType, DeviceParamConstants, FieldType, MetaExport, MetaExportDescriptor, Procedure, 
    Protocol, SonicTextCommandAttrs, UserManualAttrs, Version, CommandDef, AnswerDef,
    AnswerFieldDef, CommandContract, DeviceType,
)
from sonic_protocol.command_contracts.fields import (
    field_frequency, field_gain, field_temperature_kelvin, field_urms, field_irms, 
    field_phase, field_signal, field_ts_flag, field_swf
)
from sonic_protocol.command_contracts.transducer_commands import (
    set_frequency, get_frequency, set_swf, get_swf, get_atf, set_atf, get_att, set_att, get_atk, set_atk,
    set_gain, get_gain, set_on, set_off, get_temp, get_uipt, get_atf_list, get_att_list, get_atk_list, set_waveform, 
    get_transducer, set_transducer, get_irms
)
from sonic_protocol.command_contracts.communication_commands import (
     set_termination, set_comm_protocol, set_input_source, set_datetime, get_datetime, get_datetime_pico,
     set_log_level, 
)
from sonic_protocol.field_names import EFieldName
from sonic_protocol.command_contracts.procedure_commands import all_proc_commands, duty_cycle_proc_commands

# Version instance
version = Version(major=1, minor=0, patch=0)

"""!
    The ?protocol command is the most important command
    Without ?protocol there is no way to determine which protocol is used.
    So this command is needed.
    There should also only exist one version of this command. Because else determining the protocol version would be a nightmare.
    If you want to extend the ?protocol command. consider adding other commands
"""

field_device_type = AnswerFieldDef(
    field_name=EFieldName.DEVICE_TYPE,
    field_type=FieldType(DeviceType, converter_ref=ConverterType.ENUM),
)

get_protocol = CommandContract(
    code=CommandCode.GET_PROTOCOL,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier="?protocol"
        )
    ),
    answer_defs=AnswerDef(
        fields=[
            field_device_type,
            create_version_field(EFieldName.PROTOCOL_VERSION),
            AnswerFieldDef(
                field_name=EFieldName.IS_RELEASE, 
                field_type=FieldType(bool, converter_ref=ConverterType.BUILD_TYPE), 
            ),
            AnswerFieldDef(
                EFieldName.ADDITIONAL_OPTIONS,
                str,
                user_manual_attrs=UserManualAttrs("additional options used for future extensions of the protocol")
            )
        ]
    ),
    is_release=True
)

build_date_field = AnswerFieldDef(
    field_name=EFieldName.BUILD_DATE,
    field_type=FieldType(str)
)

build_hash_field = AnswerFieldDef(
    field_name=EFieldName.BUILD_HASH,
    field_type=FieldType(str)
)

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

get_help = CommandContract(
    code=CommandCode.GET_HELP,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier="?help"
        )
    ),
    answer_defs=AnswerDef(
        fields=[
            AnswerFieldDef(
                field_name=EFieldName.MESSAGE,
                field_type=FieldType(str)
            )
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to get help information."
    ),
    is_release=True,
    tags=["help"]
)

error_code_field = AnswerFieldDef(
    field_name=EFieldName.ERROR_CODE,
    field_type=FieldType(field_type=np.uint16)
)

procedure_field = AnswerFieldDef(
    field_name=EFieldName.PROCEDURE,
    field_type=FieldType(field_type=Procedure, converter_ref=ConverterType.ENUM),
)

get_update_worker = CommandExport(
    exports=CommandContract(
            code=CommandCode.GET_UPDATE,
            command_defs=CommandDef(
                sonic_text_attrs=SonicTextCommandAttrs(
                    string_identifier=["-", "get_update"]
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
                    field_ts_flag
                ]
            ),
            user_manual_attrs=UserManualAttrs(
                description="Mainly used by sonic control to get a short and computer friendly parsable status update."
            ),
            is_release=True,
            tags=["update", "status"]
        ),
    descriptor=MetaExportDescriptor(
        min_protocol_version=Version(major=1, minor=0, patch=0),
        included_device_types=[DeviceType.MVP_WORKER]
    )
)

get_update_descale = CommandExport(
    exports=CommandContract(
            code=CommandCode.GET_UPDATE,
            command_defs=CommandDef(
                sonic_text_attrs=SonicTextCommandAttrs(
                    string_identifier=["-", "get_update"]
                )
            ),
            answer_defs=AnswerDef(
                fields=[
                    error_code_field,
                    field_swf,
                    field_gain,
                    procedure_field,
                    field_temperature_kelvin,
                    field_irms,
                    field_signal,
                ]
            ),
            user_manual_attrs=UserManualAttrs(
                description="Mainly used by sonic control to get a short and computer friendly parsable status update."
            ),
            is_release=True,
            tags=["update", "status"]
        ),
    descriptor=MetaExportDescriptor(
        min_protocol_version=Version(major=1, minor=0, patch=0),
        included_device_types=[DeviceType.DESCALE]
    )
)

flash_usb = CommandContract(
    code=CommandCode.SET_FLASH_USB,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!FLASH_USB"]
        )
    ),
    answer_defs=AnswerDef(
        fields=[
            AnswerFieldDef(
                field_name=EFieldName.SUCCESS,
                field_type=FieldType(str)
            )
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Used for flashing the device with a new firmware."
    ),
    is_release=True,
    tags=["flashing"]
)

flash_uart9600 = CommandContract(
    code=CommandCode.SET_FLASH_9600,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!FLASH_UART_SLOW"]
        )
    ),
    answer_defs=AnswerDef(
        fields=[
            AnswerFieldDef(
                field_name=EFieldName.SUCCESS,
                field_type=FieldType(str)
            )
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Used for flashing the device with a new firmware."
    ),
    is_release=True,
    tags=["flashing"]
)

flash_uart115200 = CommandContract(
    code=CommandCode.SET_FLASH_115200,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!FLASH_UART_FAST"]
        )
    ),
    answer_defs=AnswerDef(
        fields=[
            AnswerFieldDef(
                field_name=EFieldName.SUCCESS,
                field_type=FieldType(str)
            )
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Used for flashing the device with a new firmware."
    ),
    is_release=True,
    tags=["flashing"]
)

sonic_force = CommandContract(  # Used overruling the service mode
    code=CommandCode.SONIC_FORCE,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!SONIC_FORCE", "!sonic_force"]
        )
    ),
    answer_defs=AnswerDef(
        fields=[
            AnswerFieldDef(
                field_name=EFieldName.SUCCESS,
                field_type=FieldType(str)
            )
        ]
    ),
    is_release=False,
    tags=["debugging"]
)

notify = CommandContract(
    code=CommandCode.NOTIFY_MESSAGE,
    command_defs=None,
    answer_defs=AnswerDef(
        fields=[
            AnswerFieldDef(
                field_name=EFieldName.MESSAGE,
                field_type=FieldType(str)
            )
        ]
    ),
    is_release=True,
    tags=["Notification"]
)

flash_commands: List[CommandContract] = [flash_usb, flash_uart9600, flash_uart115200]


protocol = Protocol(
    version=Version(1, 0, 0),
    consts=[
        MetaExport(
            exports=DeviceParamConstants(),
            descriptor=MetaExportDescriptor(
                min_protocol_version=Version(major=1, minor=0, patch=0),
                excluded_device_types=[DeviceType.DESCALE]
            )
        ),
        MetaExport(
            exports=DeviceParamConstants(
                max_gain=101,
            ),
            descriptor=MetaExportDescriptor(
                min_protocol_version=Version(major=1, minor=0, patch=0),
                included_device_types=[DeviceType.DESCALE]
            )
        )
    ],
    commands=[
        get_update_worker,
        get_update_descale,
        # Basic Commands needed, because they are directly used in the GUI
        CommandListExport(
            exports=[
                set_gain,
                get_gain,
                set_on,
                set_off,
                set_frequency,
                get_frequency,
                get_transducer,
                set_transducer,
            ],
            descriptor=MetaExportDescriptor(
                min_protocol_version=Version(major=0, minor=0, patch=0),
                excluded_device_types=[DeviceType.DESCALE]
            )
        ),
        CommandListExport(
            exports=[
                get_protocol,
                get_info,
                get_help,
                get_temp,
                get_uipt,
                # set_termination,
                # TODO: fix termination
                set_comm_protocol,
                set_input_source,
                set_datetime,
                get_datetime,
                get_datetime_pico,
                set_log_level,
                sonic_force,
                notify,
            ] + flash_commands,
            descriptor=MetaExportDescriptor(
                min_protocol_version=Version(major=1, minor=0, patch=0)
            )
        ),
        CommandListExport(
            exports=[
                get_atf,
                get_atf_list,
                set_atf,
                get_att,
                get_att_list,
                set_att,
                get_atk,
                get_atk_list,
                set_atk,
                set_waveform,
            ],
            descriptor = MetaExportDescriptor(
                min_protocol_version=Version(major=1, minor=0, patch=0),
                excluded_device_types=[DeviceType.DESCALE]
            )
        ),
        CommandListExport(
            exports=[
                set_gain,
                get_gain,
                set_on,
                set_off,
                get_transducer,
                set_transducer,
                set_swf,
                get_swf,
                get_irms
            ],
            descriptor = MetaExportDescriptor(
                min_protocol_version=Version(major=1, minor=0, patch=0),
                included_device_types=[DeviceType.DESCALE]
            )
        ),
        CommandListExport(
            exports=all_proc_commands,
            descriptor = MetaExportDescriptor(
                min_protocol_version=Version(major=1, minor=0, patch=0),
                excluded_device_types=[DeviceType.DESCALE]
            )
        ),
        CommandListExport(
            exports=duty_cycle_proc_commands,
            descriptor = MetaExportDescriptor(
                min_protocol_version=Version(major=1, minor=0, patch=0),
                included_device_types=[DeviceType.DESCALE]
            )
        )
    ]
)

