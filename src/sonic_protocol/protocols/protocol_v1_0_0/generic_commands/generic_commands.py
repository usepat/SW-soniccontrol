from typing import List
from sonic_protocol.defs import (
    CommandParamDef,
    FieldType,
    SonicTextCommandAttrs,
    UserManualAttrs,
    CommandDef,
    AnswerDef,
    AnswerFieldDef,
    CommandContract,
)
from sonic_protocol.command_codes import CommandCode
from sonic_protocol.protocols.protocol_v1_0_0.generic_commands.generic_fields import (
    field_device_type,
    build_date_field,
    build_hash_field,
    field_timestamp,
    param_type_timestamp,
    field_message,
)
from sonic_protocol.protocols.contract_generators import create_version_field
from sonic_protocol.field_names import EFieldName

get_info = CommandContract(
    code=CommandCode.GET_INFO,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(string_identifier="?info")
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
    is_release=True,
)

get_help = CommandContract(
    code=CommandCode.GET_HELP,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(string_identifier="?help")
    ),
    answer_def=AnswerDef(fields=[field_message]),
    user_manual_attrs=UserManualAttrs(description="Command to get help information."),
    is_release=True,
    tags=["help"],
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
            AnswerFieldDef(field_name=EFieldName.SUCCESS, field_type=FieldType(str))
        ]
    ),
    is_release=False,
    tags=["debugging"],
)

notify = CommandContract(
    code=CommandCode.NOTIFY_MESSAGE,
    command_def=None,
    answer_def=AnswerDef(fields=[field_message]),
    is_release=True,
    tags=["Notification"],
)

set_datetime = CommandContract(
    code=CommandCode.SET_DATETIME,
    command_def=CommandDef(
        setter_param=CommandParamDef(
            name=EFieldName.TIMESTAMP, param_type=param_type_timestamp
        ),
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!datetime", "set_datetime"]
        ),
    ),
    answer_def=AnswerDef(fields=[field_timestamp]),
    user_manual_attrs=UserManualAttrs(description="Command to set the datetime"),
    is_release=True,
    tags=["datetime"],
)

get_datetime = CommandContract(
    code=CommandCode.GET_DATETIME,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?datetime", "get_datetime"]
        )
    ),
    answer_def=AnswerDef(fields=[field_timestamp]),
    user_manual_attrs=UserManualAttrs(description="Command to get the datetime"),
    is_release=True,
    tags=["datetime"],
)

get_datetime_pico = CommandContract(
    code=CommandCode.GET_DATETIME_PICO,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?datetime_pico", "get_datetime_pico"]
        )
    ),
    answer_def=AnswerDef(fields=[field_timestamp]),
    user_manual_attrs=UserManualAttrs(
        description="Command to get the datetime from the rp2040"
    ),
    is_release=True,
    tags=["datetime"],
)

generic_command_contract_list: List[CommandContract] = [
    get_info,
    get_help,
    set_datetime,
    get_datetime,
    get_datetime_pico,
    notify,
    sonic_force,
]
