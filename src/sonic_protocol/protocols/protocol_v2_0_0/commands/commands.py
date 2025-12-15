import copy
from enum import Enum, IntEnum
from typing import List
from sonic_protocol.field_names import EFieldName
from sonic_protocol.schema import (
    CommandParamDef, ControlMode, ConverterType, FieldType, SIPrefix, SIUnit, SonicTextAnswerFieldAttrs, SonicTextCommandAttrs, UserManualAttrs, CommandDef, AnswerDef,
    AnswerFieldDef, CommandContract, SystemState, TransducerState, Anomaly
)
from ...protocol_v1_0_0.flashing_commands.flashing_commands import field_success
from ...protocol_v1_0_0.generic_commands.generic_fields import field_message
from ...protocol_v1_0_0.generic_commands import generic_commands as cmds
from ...protocol_v1_0_0.transducer_commands.transducer_fields import field_signal
from sonic_protocol.command_codes import CommandCode
from sonic_protocol.schema import SonicTextAnswerFieldAttrs
from sonic_protocol.protocols.protocol_v1_0_0.transducer_commands.transducer_commands import (
    get_update_worker
) 
from sonic_protocol.protocols.protocol_v1_0_0.transducer_commands.descaler_commands import (
    get_update_descale
)

from ..fields import fields as f
from ..params import params as p
import numpy as np


get_info = copy.deepcopy(cmds.get_info)
get_info.answer_def.fields.append(f.snr_field)

# Set prefix for hardware version field
for field in get_info.answer_def.fields:
    if field.field_name == EFieldName.HARDWARE_VERSION:
        field.sonic_text_attrs = SonicTextAnswerFieldAttrs(prefix="Hw: ")
    if field.field_name == EFieldName.FIRMWARE_VERSION:
        field.sonic_text_attrs = SonicTextAnswerFieldAttrs(prefix="Fw: ")



clear_errors = CommandContract(
    code=CommandCode.CLEAR_ERRORS,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!clear_errors", "clear_errors"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_success]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to clear errors"
    ),
    is_release=True,
    tags=["error"]
)

restart_device = CommandContract(
    code=CommandCode.RESTART_DEVICE,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!restart", "restart_device"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_success]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to restart device. Primarily used in debugging/testing"
    ),
    is_release=True,
    tags=["restart"]
)

get_adc = CommandContract(
    code=CommandCode.GET_ADC,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?adc", "get_adc"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_message]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to retrieve 40 adc samples"
    ),
    is_release=False,
    tags=["debug"]
)


start_configurator = CommandContract(
    code=CommandCode.START_CONFIGURATOR,
    command_def=CommandDef(
        setter_param=p.password_hashed_param,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!config", "start_configurator"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_success]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to start the configurator"
    ),
    is_release=True,
    tags=["debug"]
)

set_control_mode = CommandContract(
    code=CommandCode.SET_CONTROL_MODE,
    command_def=CommandDef(
        setter_param=CommandParamDef(
            name=EFieldName.CONTROL_MODE,
            param_type=f.field_type_control_mode
        ),
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!control", "!control_mode", "set_control_mode"]
        )
    ),
    answer_def=AnswerDef(
        fields=[f.field_control_mode]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the input source. Where to get commands from"
    ),
    is_release=True,
    tags=["communication"]
)

get_control_mode = CommandContract(
    code=CommandCode.GET_CONTROL_MODE,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?control", "?control_mode", "get_control_mode"]
        )
    ),
    answer_def=AnswerDef(
        fields=[f.field_control_mode]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to get the input source. Where to get commands from"
    ),
    is_release=True,
    tags=["communication"]
)

get_error_histo_size = CommandContract(
    code=CommandCode.GET_ERROR_HISTO_SIZE,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?error_histo", "?error_histo_size"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_message]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to get the size of error histogram logs"
    ),
    is_release=True,
    tags=["errors"]
)



pop_error_histo_message = CommandContract(
    code=CommandCode.POP_ERROR_HISTO_MESSAGE,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!pop_error_histo"]
        )
    ),
    answer_def=AnswerDef(
        fields=[f.error_message_field]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to pop error histogram messages from the error histogram log."
    ),
    is_release=True,
    tags=["errors"]
)


set_dac = CommandContract(
    code=CommandCode.SET_DAC,
    command_def=CommandDef(
        setter_param=p.param_dac_voltage,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!dac"]
        )
    ),
    answer_def=AnswerDef(
        fields=[f.field_dac_voltage]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the dac voltage."
    ),
    is_release=True,
    tags=["DAC"]
)

get_dac = CommandContract(
    code=CommandCode.GET_DAC,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?dac"]
        )
    ),
    answer_def=AnswerDef(
        fields=[f.field_dac_voltage]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to get the currently set dac voltage"
    ),
    is_release=True,
    tags=["DAC"]
)

get_update_worker_v2_0_0 = copy.deepcopy(get_update_worker)
get_update_descale_v2_0_0 = copy.deepcopy(get_update_descale)

get_update_worker_v2_0_0.answer_def.fields.extend([
    f.field_anomaly_detection, f.field_system_state
])

get_update_descale_v2_0_0.answer_def.fields.extend([
    f.field_system_state
])

for idx, field in enumerate(get_update_worker_v2_0_0.answer_def.fields):
    if field.field_name == EFieldName.ERROR_CODE:
        get_update_worker_v2_0_0.answer_def.fields[idx] = f.field_transducer_state
        get_update_descale_v2_0_0.answer_def.fields[idx] = f.field_transducer_state
        break


go_into_device_state = CommandContract(
    code=CommandCode.GO_INTO_DEVICE_STATE,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(["go_into_device_state", "!device_state"]),
        setter_param=CommandParamDef(
            EFieldName.DEVICE_STATE,
            f.field_type_device_state
        )
    ),
    answer_def=AnswerDef([f.field_device_state]),
    is_release=True
)

get_postman_update = CommandContract(
    code=CommandCode.GET_POSTMAN_UPDATE,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(["get_postman_udpate"])
    ),
    answer_def=AnswerDef([
        f.field_device_state,
        f.field_transducer_state,
        f.field_system_state
    ]),
    is_release=True
)

get_on_timer = CommandContract(
    code=CommandCode.GET_ON_TIMER,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(["?on_timer", "?on", "?ON"])
    ),
    answer_def=AnswerDef([
        f.field_days,
        f.field_hours,
        f.field_minutes
    ]),
    is_release=True
)

reset_on_timer = CommandContract(
    code=CommandCode.RESET_ON_TIMER,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(["!reset_on_timer"])
    ),
    answer_def=AnswerDef([
        field_success,
    ]),
    is_release=True
)
