import copy
from enum import Enum, IntEnum
from typing import List
from sonic_protocol.field_names import EFieldName
from sonic_protocol.schema import (
    CommandParamDef, ControlMode, FieldType, SIPrefix, SIUnit, SonicTextAnswerFieldAttrs, SonicTextCommandAttrs, UserManualAttrs, CommandDef, AnswerDef,
    AnswerFieldDef, CommandContract, SystemState, TransducerState, Anomaly
)
from sonic_protocol.command_codes import CommandCode
from sonic_protocol.schema import SonicTextAnswerFieldAttrs



# With these relative imports the path to older version can be made shorter
#from ...protocol_v2_0_0 import commands as cmd_v2

# These relative imports should always import the files form the current protocol version
from ..fields import fields as f
from ..params import params as p
from ..types import types as t
import numpy as np
from sonic_protocol.groups import GROUPS
from sonic_protocol.schema import Procedure
from ...protocol_v3_0_0.commands.commands import get_duty_cycle_v3_0_0


save_log_levels = CommandContract(
    code=CommandCode.SAVE_LOG_LEVELS,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(["!save_log", "save_log_levels"]),
    ),
    answer_def=AnswerDef([AnswerFieldDef(EFieldName.SUCCESS, FieldType(str))]),
    user_manual_attrs=UserManualAttrs(description="Saves the current logger levels for the next startup."),
    is_release=True,
    is_admin_command=True,
    group_id=GROUPS.logging,
)


field_duty_cycle_proc = AnswerFieldDef(
    EFieldName.DUTY_CYCLE_PROC, 
    FieldType(
        Procedure,
        allowed_values=(Procedure.AUTO, Procedure.RAMP, Procedure.WIPE, Procedure.NO_PROC)         
    ),
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Duty cycle proc: "),
)
field_duty_cycle_disable_psu_during_off = AnswerFieldDef(
    EFieldName.DUTY_CYCLE_DISABLE_PSU_DURING_OFF, FieldType(bool),
    sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Disable PSU during off: "),
)

set_duty_cycle_proc = CommandContract(
    code=CommandCode.SET_DUTY_CYCLE_PROC,
    command_def=CommandDef(
        setter_param=CommandParamDef(EFieldName.PROCEDURE_ARG, field_duty_cycle_proc.field_type),
        sonic_text_attrs=SonicTextCommandAttrs("!duty_cycle_proc"),
    ),
    answer_def=AnswerDef([field_duty_cycle_proc]),
    group_id=GROUPS.procedures.duty_cycle,
    user_manual_attrs=UserManualAttrs(description="Stores the duty-cycle ON-phase procedure."),
    is_release=True,
)
set_duty_cycle_disable_psu_during_off = CommandContract(
    code=CommandCode.SET_DUTY_CYCLE_DISABLE_PSU_DURING_OFF,
    command_def=CommandDef(
        setter_param=CommandParamDef(EFieldName.PROCEDURE_ARG, field_duty_cycle_disable_psu_during_off.field_type),
        sonic_text_attrs=SonicTextCommandAttrs("!duty_cycle_disable_psu_during_off"),
    ),
    answer_def=AnswerDef([field_duty_cycle_disable_psu_during_off]),
    group_id=GROUPS.procedures.duty_cycle,
    user_manual_attrs=UserManualAttrs(description="Stores whether to disable the PSU during the OFF phase. Runtime switching is not implemented yet."),
    is_release=True,
)
get_duty_cycle = copy.deepcopy(get_duty_cycle_v3_0_0)
get_duty_cycle.answer_def.fields.extend([
    field_duty_cycle_proc, field_duty_cycle_disable_psu_during_off,
])




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
