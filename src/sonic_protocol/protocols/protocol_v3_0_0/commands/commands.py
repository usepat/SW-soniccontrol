import copy
from enum import Enum, IntEnum
from typing import List
from sonic_protocol.field_names import EFieldName
from sonic_protocol.schema import (
    CommandParamDef, ControlMode, ConverterType, FieldType, Loglevel, SIPrefix, SIUnit, SonicTextAnswerFieldAttrs, SonicTextCommandAttrs, UserManualAttrs, CommandDef, AnswerDef,
    AnswerFieldDef, CommandContract, SystemState, TransducerState, Anomaly
)
from sonic_protocol.command_codes import CommandCode
from sonic_protocol.schema import SonicTextAnswerFieldAttrs



# With these relative imports the path to older version can be made shorter
from ...protocol_v2_0_0.commands import commands as cmd_v2
from ...protocol_v1_0_0.transducer_commands import transducer_commands as trcmd_v1
from ...protocol_v1_0_0.procedure_commands import procedure_commands as prcmd_v1
from sonic_protocol.protocols.protocol_v1_0_0.transducer_commands.transducer_fields import (
    param_index
)

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

get_ramp_v3_0_0 = copy.deepcopy(prcmd_v1.get_ramp)
get_ramp_v3_0_0.answer_def.fields.append(
    f.field_ramp_gain
)

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

get_uipt_raw = CommandContract(
    CommandCode.GET_UIPT_RAW,
    CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs("?uipt_raw")
    ),
    AnswerDef([f.raw_urms_field, f.raw_irms_field, f.raw_phase_field, f.raw_tsflag_field]),
    is_release=False
)


set_log_level_v3_0_0 = CommandContract(
    code=CommandCode.SET_LOG_LEVEL,
    command_def=CommandDef(
        index_param=CommandParamDef(
            name=EFieldName.LOGGER_NAME,
            param_type=FieldType(
                field_type=str
            )
        ),
        setter_param=CommandParamDef(
            name=EFieldName.LOG_LEVEL,
            param_type=FieldType(
                field_type=Loglevel,
                converter_ref=ConverterType.ENUM
            )
        ),
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!log", "set_log_level"]
        )
    ),
    answer_def=AnswerDef(
        fields=[
            AnswerFieldDef(
                field_name=EFieldName.LOGGER_NAME,
                field_type=FieldType(
                    field_type=str
                ),
                sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="Set ", postfix=r" log level to \\") # Escape the # character
            ),
            AnswerFieldDef(
                field_name=EFieldName.LOG_LEVEL,
                field_type=FieldType(
                    field_type=Loglevel,
                    converter_ref=ConverterType.ENUM
                )   
            )
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the log level"
    ),
    is_release=True,
    tags=["log"]
)

get_logger_list_size = CommandContract(
    code=CommandCode.GET_LOGGER_LIST_SIZE,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(string_identifier="?num_loggers")
    ),
    answer_def=AnswerDef([
        AnswerFieldDef(EFieldName.COUNT, field_type=FieldType(field_type=np.uint8))
    ]),
    user_manual_attrs=UserManualAttrs(
        description="Retrieve the amount of loggers available"
    ),
    is_release=True,
    tags=["log"]
)

get_logger_list_item = CommandContract(
    code=CommandCode.GET_LOGGER_LIST_ITEM,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(string_identifier="?logger"),
        index_param=CommandParamDef(EFieldName.INDEX, FieldType(np.uint8))
    ),
    answer_def=AnswerDef([
        AnswerFieldDef(EFieldName.LOGGER_NAME, FieldType(str)),
        AnswerFieldDef(EFieldName.LOG_LEVEL, FieldType(Loglevel, converter_ref=ConverterType.ENUM))
    ]),
    user_manual_attrs=UserManualAttrs(
        description="Retrieve the name and log level of the logger with the specified id"
    ),
    is_release=True,
    tags=["log"]
)

get_connection_status = CommandContract(
    code=CommandCode.GET_CONNECTION_STATUS,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs("?connection")
    ),
    answer_def=AnswerDef(
        [f.connection_status_field]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Returns true if the postman is connected to a worker"
    ),
    is_release=True,
    tags=["postman"]
)

get_num_tests = CommandContract(
    code=CommandCode.GET_NUM_TESTS,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs("?num_tests")
    ),
    answer_def=AnswerDef(
        [f.count_field]
    ),
    is_release=True,
    tags=["testing"]
)

get_test_info = CommandContract(
    code=CommandCode.GET_TEST_INFO,
    command_def=CommandDef(
        index_param=p.param_index_uint8,
        sonic_text_attrs=SonicTextCommandAttrs("?test_info")
    ),
    answer_def=AnswerDef( [
        f.test_name_field,
        f.test_suite_name_field
    ]),
    is_release=True,
    tags=["testing"]
)

run_test = CommandContract(
    code=CommandCode.RUN_TEST,
    command_def=CommandDef(
        index_param=p.param_index_uint8,
        sonic_text_attrs=SonicTextCommandAttrs("!run_test")
    ),
     answer_def=AnswerDef( [
        AnswerFieldDef(EFieldName.TEST_RESULT, FieldType(t.TestResult, converter_ref=ConverterType.ENUM)),
        AnswerFieldDef(EFieldName.TEST_INTERACTION, FieldType(t.TestInteraction, converter_ref=ConverterType.ENUM)),
        AnswerFieldDef(EFieldName.MESSAGE, FieldType(str))
    ]),
    is_release=True,
    tags=["testing"]
)

start_diagnostic_tool = CommandContract(
    code=CommandCode.START_DIAGNOSTIC_TOOL,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs("!start_diagnostic_tool")
    ),
    answer_def=AnswerDef([
        AnswerFieldDef(EFieldName.SUCCESS, FieldType(str))
    ]),
    is_release=True,
    tags=["testing", "diagnosis", "debugging"]
)

start_operator = CommandContract(
    code=CommandCode.START_OPERATOR,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs("!start_operator")
    ),
    answer_def=AnswerDef([
        AnswerFieldDef(EFieldName.SUCCESS, FieldType(str))
    ]),
    is_release=True
)

