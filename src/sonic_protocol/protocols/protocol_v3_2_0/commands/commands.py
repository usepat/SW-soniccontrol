import copy
from enum import Enum, IntEnum
from typing import List
from sonic_protocol.field_names import EFieldName
from sonic_protocol.groups import GROUPS
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


get_memory_region_info = CommandContract(
    code=CommandCode.GET_MEMORY_REGION_INFO,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(string_identifier="?memory_region_info"),
        index_param=CommandParamDef(EFieldName.INDEX, param_type=np.uint8, user_manual_attrs=UserManualAttrs("index of the memory region"))
    ),
    answer_def=AnswerDef([
        AnswerFieldDef(EFieldName.NAME, str),
        AnswerFieldDef(EFieldName.ADDRESS, np.uint32),
        AnswerFieldDef(EFieldName.SIZE, np.uint32),
        AnswerFieldDef(EFieldName.EXISTS_NEXT, bool, user_manual_attrs=UserManualAttrs("if set to true, then it means that for the next index also a memory region exists. Can be used to iterate the regions like a linked list"))
    ]),
     user_manual_attrs=UserManualAttrs(
        description="This function is used mainly for the bootloader. So that we can see what was installed on the pico"
    ),
    is_release=True,
    is_admin_command=True,
    group_id=GROUPS.misc,
    tags=["memory"]
)

