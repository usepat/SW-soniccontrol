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
#from ...protocol_v2_0_0 import commands as cmd_v2

# These relative imports should always import the files form the current protocol version
from ..fields import fields as f
from ..params import params as p
from ..types import types as t
import numpy as np




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
