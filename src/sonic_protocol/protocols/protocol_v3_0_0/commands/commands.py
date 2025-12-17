import copy
from enum import Enum, IntEnum
from typing import List
from sonic_protocol.field_names import EFieldName
from sonic_protocol.schema import (
    CommandParamDef, ControlMode, ConverterType, FieldType, SIPrefix, SIUnit, SonicTextAnswerFieldAttrs, SonicTextCommandAttrs, UserManualAttrs, CommandDef, AnswerDef,
    AnswerFieldDef, CommandContract, SystemState, TransducerState, Anomaly
)
from sonic_protocol.command_codes import CommandCode
from sonic_protocol.schema import SonicTextAnswerFieldAttrs



# With these relative imports the path to older version can be made shorter
from ...protocol_v2_0_0.commands import commands as cmd_v2
from ...protocol_v1_0_0.transducer_commands import transducer_commands as trcmd_v1
from ...protocol_v1_0_0.procedure_commands import procedure_commands as prcmd_v1

# These relative imports should always import the files form the current protocol version
from ..fields import fields as f
from ..params import params as p
from ..types import types as t
import numpy as np

get_update_worker_v3_0_0 = copy.deepcopy(cmd_v2.get_update_worker_v2_0_0)

for idx, field in enumerate(get_update_worker_v3_0_0.answer_def.fields):
    if field.field_name == EFieldName.IRMS:
        get_update_worker_v3_0_0.answer_def.fields[idx] = f.irms_field
    if field.field_name == EFieldName.URMS:
        get_update_worker_v3_0_0.answer_def.fields[idx] = f.urms_field
    if field.field_name == EFieldName.PHASE:
        get_update_worker_v3_0_0.answer_def.fields[idx] = f.phase_field
    if field.field_name == EFieldName.TS_FLAG:
        get_update_worker_v3_0_0.answer_def.fields[idx] = f.ts_flag_field
    # if field.field_name == EFieldName.FREQUENCY:
    #     get_update_worker_v3_0_0.answer_def.fields[idx] = f.frequency_field

get_update_descale_v3_0_0 = copy.deepcopy(cmd_v2.get_update_descale_v2_0_0)
for idx, field in enumerate(get_update_descale_v3_0_0.answer_def.fields):
    if field.field_name == EFieldName.IRMS:
        get_update_descale_v3_0_0.answer_def.fields[idx] = f.irms_field


get_frequency_v3_0_0 = copy.deepcopy(trcmd_v1.get_frequency)
for idx, field in enumerate(get_frequency_v3_0_0.answer_def.fields):
    if field.field_name == EFieldName.FREQUENCY:
        get_frequency_v3_0_0.answer_def.fields[idx] = f.frequency_field

set_frequency_v3_0_0 = copy.deepcopy(trcmd_v1.set_frequency)
assert(set_frequency_v3_0_0.command_def)
set_frequency_v3_0_0.command_def.setter_param = p.frequency_param
for idx, field in enumerate(set_frequency_v3_0_0.answer_def.fields):
    if field.field_name == EFieldName.FREQUENCY:
        set_frequency_v3_0_0.answer_def.fields[idx] = f.frequency_field

get_atf_v3_0_0 = copy.deepcopy(trcmd_v1.get_atf)
for idx, field in enumerate(get_atf_v3_0_0.answer_def.fields):
    if field.field_name == EFieldName.ATF:
        get_atf_v3_0_0.answer_def.fields[idx] = f.atf_field

set_atf_v3_0_0 = copy.deepcopy(trcmd_v1.set_atf)
assert(set_atf_v3_0_0.command_def)
set_atf_v3_0_0.command_def.setter_param = p.atf_param
for idx, field in enumerate(set_atf_v3_0_0.answer_def.fields):
    if field.field_name == EFieldName.ATF:
        set_atf_v3_0_0.answer_def.fields[idx] = f.atf_field

set_ramp_gain = CommandContract(
    CommandCode.SET_RAMP_GAIN,
    CommandDef(
        setter_param=CommandParamDef(
            EFieldName.PROCEDURE_ARG,
            f.field_type_gain
        ), 
        sonic_text_attrs=SonicTextCommandAttrs("!ramp_gain")
    ),
    AnswerDef([f.field_ramp_gain]),
    is_release=True
)

# get_ramp = copy.deepcopy(prcmd_v1.get_ramp)

# for field in get_ramp.answer_def.fields:
#     if field.field_name == EFieldName.RAMP_F_START:
#         field = f.field_ramp_f_start
#     if field.field_name == EFieldName.RAMP_F_STOP:
#         field = f.field_ramp_f_stop

# set_ramp_f_start = prcmd_v1.generate_procedure_arg_setter_contract(
#     CommandCode.SET_RAMP_F_START, 
#     ["!ramp_f_start"],
#     response_field=f.field_ramp_f_start 
# )

# set_ramp_f_stop = prcmd_v1.generate_procedure_arg_setter_contract(
#     CommandCode.SET_RAMP_F_STOP, 
#     ["!ramp_f_stop"],
#     response_field=f.field_ramp_f_stop 
# )

# example_command = CommandContract(
#     code=CommandCode.{CODE},
#     command_def=CommandDef(
#         index_param={index_param},
#         setter_param={setter_param},
#         sonic_text_attrs=SonicTextCommandAttrs(
#             string_identifier=["{!command_identifier}"]
#         )
#     ),
#     answer_def=AnswerDef(
#         fields=[{answer_fields}]
#     ),
#     user_manual_attrs=UserManualAttrs(
#         description="{description}"
#     ),
#     is_release=True,
#     tags=["{tag}"]
# )
