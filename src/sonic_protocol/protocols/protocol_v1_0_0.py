from typing import Any, Dict
import numpy as np
from sonic_protocol.command_contracts.contract_generators import create_version_field
from sonic_protocol.defs import (
    CommandCode, ConverterType, DeviceParamConstantType, FieldType, Procedure, 
    ProtocolType, SonicTextCommandAttrs, UserManualAttrs, Version, CommandDef, AnswerDef,
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
from sonic_protocol.protocol_list import ProtocolList
from sonic_protocol.command_contracts.unknown_commands import (
    unknown_get_frequency, unknown_get_gain, unknown_get_transducer, unknown_set_frequency, 
    unknown_set_gain, unknown_set_off, unknown_set_on, unknown_set_transducer
)
from sonic_protocol.command_contracts.crystal_command_contracts import crystal_commands, crystal_constants


# TODO: move version and fields into own files 

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
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier="?protocol"
        )
    ),
    answer_def=AnswerDef(
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
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier="?info"
        )
    ),
    answer_def=AnswerDef(
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
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier="?help"
        )
    ),
    answer_def=AnswerDef(
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

get_update_worker = CommandContract(
    code=CommandCode.GET_UPDATE,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["-", "get_update"]
        )
    ),
    answer_def=AnswerDef(
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
)

get_update_descale = CommandContract(
    code=CommandCode.GET_UPDATE,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["-", "get_update"]
        )
    ),
    answer_def=AnswerDef(
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
)


flash_usb = CommandContract(
    code=CommandCode.SET_FLASH_USB,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!FLASH_USB"]
        )
    ),
    answer_def=AnswerDef(
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
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!FLASH_UART_SLOW"]
        )
    ),
    answer_def=AnswerDef(
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
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!FLASH_UART_FAST"]
        )
    ),
    answer_def=AnswerDef(
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
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!SONIC_FORCE", "!sonic_force"]
        )
    ),
    answer_def=AnswerDef(
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
    command_def=None,
    answer_def=AnswerDef(
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

saveSettings = CommandContract(
    code=CommandCode.SET_SETTINGS,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!saveSettings", "!commission"]
        )
    ),
    answer_def=AnswerDef(
        fields=[
            AnswerFieldDef(
                field_name=EFieldName.SUCCESS,
                field_type=FieldType(str)
            )
        ]
    ),
    is_release=True,
    tags=["Settings", "Commissioning"]
)

notify_proc_failure = CommandContract(
    code=CommandCode.NOTIFY_PROCEDURE_FAILURE,
    command_def=None,
    answer_def=AnswerDef(
        fields=[
            AnswerFieldDef(
                field_name=EFieldName.ERROR_MESSAGE,
                field_type=FieldType(str)
            )
        ]
    ),
    is_release=True,
    tags=["Notification", "Procedure"]
)

class Protocol_v1_0_0(ProtocolList):
    @property
    def version(self) -> Version:
        return Version(1, 0, 0)
    
    @property
    def previous_protocol(self) -> ProtocolList | None:
        return None

    def supports_device_type(self, device_type: DeviceType) -> bool:
        return device_type in [DeviceType.MVP_WORKER, DeviceType.DESCALE, DeviceType.CRYSTAL, DeviceType.UNKNOWN]

    def _get_command_contracts_for(self, protocol_type: ProtocolType) -> Dict[CommandCode, CommandContract | None]:
        command_contract_list =  [] 

        match protocol_type.device_type:
            case DeviceType.DESCALE:
                command_contract_list.extend([
                    get_update_descale,
                    set_swf,
                    get_swf,
                    get_irms
                ])
                command_contract_list.extend(duty_cycle_proc_commands)
            case DeviceType.MVP_WORKER: 
                command_contract_list.extend([
                    get_update_worker,
                    set_frequency,
                    get_frequency,
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
                ])
                command_contract_list.extend(all_proc_commands)
            case DeviceType.UNKNOWN:
                command_contract_list.extend([
                    get_protocol,
                    unknown_get_frequency,
                    unknown_set_frequency,
                    unknown_get_transducer,
                    unknown_set_transducer,
                    unknown_set_on,
                    unknown_set_off,
                    unknown_get_gain,
                    unknown_set_gain,
                ])
            case DeviceType.CRYSTAL:
                command_contract_list.append(get_info)
                command_contract_list.extend(crystal_commands)
            case _:
                assert False, "Unreachable"

        if protocol_type.device_type in [DeviceType.DESCALE, DeviceType.MVP_WORKER]:
            command_contract_list.extend([
                    get_protocol,
                    get_info,
                    get_help,

                    set_gain,
                    get_gain,
                    get_temp,
                    get_uipt,
                    set_on,
                    set_off,

                    get_transducer,
                    set_transducer,

                    set_termination,
                    # TODO: fix termination
                    set_comm_protocol,
                    set_input_source,
                    set_datetime,
                    get_datetime,
                    get_datetime_pico,
                    set_log_level,
                    sonic_force,
                    notify,
                    saveSettings,

                    flash_usb, 
                    flash_uart9600, 
                    flash_uart115200
            ])

        return { command_contract.code: command_contract for command_contract in command_contract_list }

    def _get_device_constants_for(self, protocol_type: ProtocolType) -> Dict[DeviceParamConstantType, Any]:
        match protocol_type.device_type:
            case DeviceType.DESCALE:
                return { DeviceParamConstantType.MAX_GAIN: 101 }
            case DeviceType.CRYSTAL:
                return crystal_constants
            case _:
                return {}
