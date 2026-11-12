import copy
from enum import Enum, IntEnum
from typing import List
from sonic_protocol.field_names import EFieldName
from sonic_protocol.groups import GROUPS
from sonic_protocol.schema import (
    CommandParamDef, ControlMode, FieldType, NumStrEnum, NumStrValue, Procedure, SIPrefix, SIUnit, SonicTextAnswerFieldAttrs, SonicTextCommandAttrs, UserManualAttrs, CommandDef, AnswerDef,
    AnswerFieldDef, CommandContract, SystemState, TransducerState, Anomaly, Version
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

class PluginVarType(NumStrEnum):
    UINT32 = NumStrValue(2, "uint32")
    FLOAT32 = NumStrValue(3, "float32")
    STR = NumStrValue(4, "str")
    BOOL = NumStrValue(5, "bool")


plugin_index_param = CommandParamDef(
    name=EFieldName.PLUGIN_INDEX,
    param_type=FieldType(np.uint8)
)
index_param = CommandParamDef(
    name=EFieldName.INDEX,
    param_type=FieldType(np.uint8)
)
plugin_name_param = CommandParamDef(
    name=EFieldName.PLUGIN_NAME,
    param_type=FieldType(str)
)
plugin_var_name_param = CommandParamDef(
    name=EFieldName.NAME,
    param_type=FieldType(str)
)
plugin_action_name_param = CommandParamDef(
    name=EFieldName.NAME,
    param_type=FieldType(str)
)

get_num_plugins = CommandContract(
    code=CommandCode.GET_NUM_PLUGINS,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?num_plugins"]
        )
    ),
    answer_def=AnswerDef(
        fields=[
            AnswerFieldDef(EFieldName.COUNT, FieldType(np.uint8))
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="gets the number of available plugins"
    ),
    is_release=True,
    group_id=GROUPS.plugin
)

get_plugin_info = CommandContract(
    code=CommandCode.GET_PLUGIN_INFO,
    command_def=CommandDef(
        index_param=plugin_index_param,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?plugin_info"]
        )
    ),
    answer_def=AnswerDef(
        fields=[
            AnswerFieldDef(EFieldName.INDEX, FieldType(np.uint8)),
            AnswerFieldDef(EFieldName.NAME, FieldType(str)),
            AnswerFieldDef(EFieldName.VERSION, FieldType(Version)),
            AnswerFieldDef(EFieldName.NUM_VARIABLES, FieldType(np.uint8)),
            AnswerFieldDef(EFieldName.NUM_ACTIONS, FieldType(np.uint8)),
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="gets the metadata for the specified plugin"
    ),
    is_release=True,
    group_id=GROUPS.plugin
)

get_plugin_var_info = CommandContract(
    code=CommandCode.GET_PLUGIN_VAR_INFO,
    command_def=CommandDef(
        params=[plugin_index_param, index_param],
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?plugin_var_info"]
        )
    ),
    answer_def=AnswerDef(
        fields=[
            AnswerFieldDef(EFieldName.INDEX, FieldType(np.uint8)),
            AnswerFieldDef(EFieldName.NAME, FieldType(str)),
            AnswerFieldDef(EFieldName.TYPE, FieldType(field_type=PluginVarType)),
            AnswerFieldDef(EFieldName.IS_WRITABLE, FieldType(field_type=bool)),
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="gets the metadata for a plugin variable"
    ),
    is_release=True,
    group_id=GROUPS.plugin
)

def create_set_plugin_var_command_contract(command_code: CommandCode, field_type, command_identifiers: str | List[str]):
    return CommandContract(
        code=command_code,
        command_def=CommandDef(
            params=[plugin_name_param, plugin_var_name_param],
            setter_param=CommandParamDef(EFieldName.VALUE, FieldType(field_type)),
            sonic_text_attrs=SonicTextCommandAttrs(
                string_identifier=command_identifiers
            )
        ),
        answer_def=AnswerDef(
            fields=[
                AnswerFieldDef(EFieldName.SUCCESS, FieldType(str))
            ]
        ),
        user_manual_attrs=UserManualAttrs(
            description="sets the plugin variable with appropriate type. Returns error on type mismatch"
        ),
        is_release=True,
        group_id=GROUPS.plugin
    )

def create_get_plugin_var_command_contract(command_code: CommandCode, field_type, command_identifiers: str | List[str]):
    return CommandContract(
        code=command_code,
        command_def=CommandDef(
            params=[plugin_name_param, plugin_var_name_param],
            sonic_text_attrs=SonicTextCommandAttrs(
                string_identifier=[command_identifiers]
            )
        ),
        answer_def=AnswerDef(
            fields=[
                AnswerFieldDef(EFieldName.VALUE, FieldType(field_type))
            ]
        ),
        user_manual_attrs=UserManualAttrs(
            description="gets the plugin variable with appropriate type. Returns error on type mismatch"
        ),
        is_release=True,
        group_id=GROUPS.plugin
    )


set_plugin_uint_var = create_set_plugin_var_command_contract(
    CommandCode.SET_PLUGIN_UINT_VAR,
    np.uint32,
    "!plugin_uint_var"
)
set_plugin_float_var = create_set_plugin_var_command_contract(
    CommandCode.SET_PLUGIN_FLOAT_VAR,
    float,
    "!plugin_float_var"
)
set_plugin_bool_var = create_set_plugin_var_command_contract(
    CommandCode.SET_PLUGIN_BOOL_VAR,
    bool,
    "!plugin_bool_var"
)

get_plugin_uint_var = create_get_plugin_var_command_contract(
    CommandCode.GET_PLUGIN_UINT_VAR,
    np.uint32,
    "?plugin_uint_var"
)
get_plugin_float_var = create_get_plugin_var_command_contract(
    CommandCode.GET_PLUGIN_FLOAT_VAR,
    float,
    "?plugin_float_var"
)
get_plugin_bool_var = create_get_plugin_var_command_contract(
    CommandCode.GET_PLUGIN_BOOL_VAR,
    bool,
    "?plugin_bool_var"
)
get_plugin_str_var = create_get_plugin_var_command_contract(
    CommandCode.GET_PLUGIN_STR_VAR,
    str,
    "?plugin_str_var"
)

get_plugin_action_info = CommandContract(
    code=CommandCode.GET_PLUGIN_ACTION_INFO,
    command_def=CommandDef(
        params=[plugin_index_param, index_param],
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?plugin_action_info"]
        )
    ),
    answer_def=AnswerDef(
        fields=[
            AnswerFieldDef(EFieldName.INDEX, FieldType(np.uint8)),
            AnswerFieldDef(EFieldName.NAME, FieldType(str)),
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="gets the metadata for a plugin action"
    ),
    is_release=True,
    group_id=GROUPS.plugin
)

do_plugin_action = CommandContract(
    code=CommandCode.DO_PLUGIN_ACTION,
    command_def=CommandDef(
        params=[plugin_name_param, plugin_action_name_param],
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!do_plugin_action"]
        )
    ),
    answer_def=AnswerDef(
        fields=[
            AnswerFieldDef(EFieldName.ERROR_CODE, FieldType(np.uint8)),
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="executes a plugin action. Returns an error code. Plugin should follow C standard. 0 means success"
    ),
    is_release=True,
    group_id=GROUPS.plugin
)

enable_plugin = CommandContract(
    code=CommandCode.ENABLE_PLUGIN,
    command_def=CommandDef(
        params=[plugin_name_param],
        setter_param=CommandParamDef(EFieldName.ENABLED, FieldType(bool)),
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!enable_plugin"]
        )
    ),
    answer_def=AnswerDef(
        fields=[
            AnswerFieldDef(EFieldName.SUCCESS, FieldType(str))
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="enables or disables a plugin"
    ),
    is_release=True,
    group_id=GROUPS.plugin
)

run_proc = CommandContract(
    code=CommandCode.RUN_PROC,
    command_def=CommandDef(
        index_param=CommandParamDef(EFieldName.PROCEDURE, FieldType(Procedure)),
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!run_proc", "run_proc"]
        )
    ),
    answer_def=AnswerDef(
        fields=[
            AnswerFieldDef(EFieldName.PROCEDURE, FieldType(Procedure), 
                           sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="proc: "))
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="starts a procedure"
    ),
    is_release=True,
    group_id=GROUPS.procedures.procedure
)


