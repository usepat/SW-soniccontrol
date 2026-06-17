import copy
from enum import Enum, IntEnum
from typing import List
from sonic_protocol.field_names import EFieldName
from sonic_protocol.groups import GROUPS
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
from sonic_protocol.protocols.protocol_v1_0_0.procedure_commands.procedure_commands import (
    set_duty_cycle_t_off, set_duty_cycle_t_on, get_duty_cycle
)
# These relative imports should always import the files form the current protocol version
from ..fields import fields as f
from ..params import params as p
from ..types import types as t
import numpy as np

get_update_worker_v3_0_0 = copy.deepcopy(cmd_v2.get_update_worker_v2_0_0)
get_update_worker_v3_0_0.code = CommandCode.GET_UPDATE_WORKER_V3_0_0
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
get_update_descale_v3_0_0.code = CommandCode.GET_UPDATE_DESCALE_V3_0_0
irms_index = None
for idx, field in enumerate(get_update_descale_v3_0_0.answer_def.fields):
    if field.field_name == EFieldName.IRMS:
        get_update_descale_v3_0_0.answer_def.fields[idx] = f.irms_field
        irms_index = idx
        break
assert irms_index is not None, "IRMS fieldname not found in descale update command"
get_update_descale_v3_0_0.answer_def.fields.insert(irms_index + 1, f.ipp_field)

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
    group_id=GROUPS.procedures.ramp,
    user_manual_attrs=UserManualAttrs(description="Sets the Ramp gain."),
    is_release=True
)

get_uipt_raw = CommandContract(
    CommandCode.GET_UIPT_RAW,
    CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs("?uipt_raw")
    ),
    AnswerDef([f.raw_urms_field, f.raw_irms_field, f.raw_phase_field, f.raw_tsflag_field]),
    group_id=GROUPS.measurements,
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
                )
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
        description="Sets the logger level for the selected logger."
    ),
    is_release=True,
    group_id=GROUPS.logging,
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
        description="Retrieves the number of available loggers."
    ),
    is_release=True,
    group_id=GROUPS.logging,
    tags=["log"]
)

get_logger_list_item = CommandContract(
    code=CommandCode.GET_LOGGER_LIST_ITEM,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(string_identifier="?logger"),
        index_param=p.param_index_uint8
    ),
    answer_def=AnswerDef([
        AnswerFieldDef(EFieldName.LOGGER_NAME, FieldType(str)),
        AnswerFieldDef(EFieldName.LOG_LEVEL, FieldType(Loglevel, converter_ref=ConverterType.ENUM))
    ]),
    user_manual_attrs=UserManualAttrs(
        description="Retrieves the logger name and level for the specified logger ID."
    ),
    is_release=True,
    group_id=GROUPS.logging,
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
        description="Returns whether the postman is connected to a worker."
    ),
    is_release=True,
    group_id=GROUPS.generic,
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
    user_manual_attrs=UserManualAttrs(description="Retrieves the number of available tests."),
    group_id=GROUPS.testing,
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
    user_manual_attrs=UserManualAttrs(description="Retrieves test metadata (name and suite) for the specified test index."),
    group_id=GROUPS.testing,
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
        AnswerFieldDef(EFieldName.TEST_STEP_INDEX, FieldType(np.uint8), sonic_text_attrs=SonicTextAnswerFieldAttrs(prefix="test step: ")),
        AnswerFieldDef(EFieldName.TEST_INTERACTION, FieldType(t.TestInteraction, converter_ref=ConverterType.ENUM)),
        AnswerFieldDef(EFieldName.NUM_TEST_VALIDATION_ARGS, FieldType(np.uint8)),
        AnswerFieldDef(EFieldName.MESSAGE, FieldType(str)),
    ]),
    is_release=True,
    user_manual_attrs=UserManualAttrs(description="Runs the specified test."),
    group_id=GROUPS.testing,
    tags=["testing"]
)

abort_test = CommandContract(
    code=CommandCode.ABORT_TEST,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs("!abort_test")
    ),
    answer_def=AnswerDef([
        AnswerFieldDef(EFieldName.SUCCESS, FieldType(str))
    ]),
    is_release=True,
    user_manual_attrs=UserManualAttrs(description="Aborts the currently running test."),
    group_id=GROUPS.testing,
    tags=["testing"]
)

get_test_validation_arg = CommandContract(
    code=CommandCode.GET_TEST_VALIDATION_ARG,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs("?test_validation_arg"),
        index_param=p.param_index_uint8
    ),
    answer_def=AnswerDef([
        AnswerFieldDef(EFieldName.NAME, FieldType(str)),
        AnswerFieldDef(EFieldName.VALUE, FieldType(float)),
    ]),
    is_release=True,
    user_manual_attrs=UserManualAttrs(description="Fetches an argument needed for user validation"),
    group_id=GROUPS.testing,
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
    user_manual_attrs=UserManualAttrs(description="Starts the diagnostic tool on the device."),
    group_id=GROUPS.generic,
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
    is_release=True,
    user_manual_attrs=UserManualAttrs(description="Starts operator mode on the device."),
    group_id=GROUPS.generic,
)


set_dac_mV = CommandContract(
    code=CommandCode.SET_DAC,
    command_def=CommandDef(
        setter_param=p.param_dac_mV,
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!dac"]
        )
    ),
    answer_def=AnswerDef(
        fields=[f.dac_mV_field]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Sets the DAC voltage in millivolts."
    ),
    is_release=False,
    group_id=GROUPS.transducer,
    tags=["DAC"]
)

get_modbus_settings = CommandContract(
    code=CommandCode.GET_MODBUS_SETTINGS,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?modbus_settings"]
        )
    ),
    answer_def=AnswerDef(
        fields=[
            f.modbus_server_id_field,
            f.baudrate_field,
            f.uart_interface_field,
            f.parity_field
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Returns the settings for modbus over serial line"
    ),
    is_release=True,
    group_id=GROUPS.communication.serial_settings
)


set_modbus_server_id = CommandContract(
    code=CommandCode.SET_MODBUS_SLAVE_ADDRESS,
    command_def=CommandDef(
        setter_param=CommandParamDef(EFieldName.MODBUS_SERVER_ID, f.field_type_modbus_server_id),
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!modbus_server_id"]
        )
    ),
    answer_def=AnswerDef(
        fields=[
            f.modbus_server_id_field,
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Sets the modbus server id."
    ),
    is_release=True,
    group_id=GROUPS.communication.serial_settings
)

set_modbus_baudrate = CommandContract(
    code=CommandCode.SET_MODBUS_BAUDRATE,
    command_def=CommandDef(
        setter_param=CommandParamDef(EFieldName.BAUDRATE, f.field_type_baudrate),
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!modbus_baudrate"]
        )
    ),
    answer_def=AnswerDef(
        fields=[
            f.baudrate_field,
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Sets the baudrate for modbus over serial line."
    ),
    is_release=True,
    group_id=GROUPS.communication.serial_settings
)

set_modbus_uart_interface = CommandContract(
    code=CommandCode.SET_MODBUS_INTERFACE,
    command_def=CommandDef(
        setter_param=CommandParamDef(EFieldName.UART_INTERFACE, f.field_type_uart_interface),
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!modbus_uart_interface"]
        )
    ),
    answer_def=AnswerDef(
        fields=[
            f.uart_interface_field,
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Sets the physical interface for modbus over serial line."
    ),
    is_release=True,
    group_id=GROUPS.communication.serial_settings
)

set_modbus_parity = CommandContract(
    code=CommandCode.SET_MODBUS_PARITY,
    command_def=CommandDef(
        setter_param=CommandParamDef(EFieldName.PARITY, f.field_type_parity),
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!modbus_parity"]
        )
    ),
    answer_def=AnswerDef(
        fields=[
            f.parity_field,
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Sets the parity for modbus over serial line."
    ),
    is_release=True,
    group_id=GROUPS.communication.serial_settings
)

start_customizer = CommandContract(
    code=CommandCode.START_CUSTOMIZER,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!start_customizer"]
        )
    ),
    answer_def=AnswerDef(
        fields=[f.field_success]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Starts the customizer, e.g. used for modbus settings."
    ),
    is_release=True,
    group_id=GROUPS.generic,
)


set_duty_cycle_t_off_v3_0_0 = copy.deepcopy(set_duty_cycle_t_off)
set_duty_cycle_t_off_v3_0_0.answer_def.replace_field_def(f.field_duty_cycle_t_off_v3_0_0)

set_duty_cycle_t_on_v3_0_0 = copy.deepcopy(set_duty_cycle_t_on)
set_duty_cycle_t_on_v3_0_0.answer_def.replace_field_def(f.field_duty_cycle_t_on_v3_0_0)

get_duty_cycle_v3_0_0 = copy.deepcopy(get_duty_cycle)
get_duty_cycle_v3_0_0.answer_def.replace_field_def(f.field_duty_cycle_t_off_v3_0_0)
get_duty_cycle_v3_0_0.answer_def.replace_field_def(f.field_duty_cycle_t_on_v3_0_0)


get_num_allocators = CommandContract(
    code=CommandCode.GET_NUM_ALLOCATORS,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(string_identifier="?num_allocators")
    ),
    answer_def=AnswerDef([
        AnswerFieldDef(EFieldName.COUNT, field_type=FieldType(field_type=np.uint8))
    ]),
    user_manual_attrs=UserManualAttrs(
        description="Retrieves the number of internal allocators."
    ),
    is_release=False,
    group_id=GROUPS.logging,
    tags=["log", "performance"]
)

get_allocator_stats = CommandContract(
    code=CommandCode.GET_ALLOCATOR_STATS,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(string_identifier="?allocator_stats"),
        index_param=p.param_index_uint8
    ),
    answer_def=AnswerDef([
        AnswerFieldDef(EFieldName.ALLOCATOR_NAME, FieldType(str)),
        AnswerFieldDef(EFieldName.INDEX, FieldType(field_type=np.uint8), UserManualAttrs("parent index. Allocators are hierarchical")),
        AnswerFieldDef(EFieldName.SIZE, FieldType(field_type=np.uint32)),
        AnswerFieldDef(EFieldName.CURRENT_ALLOCATIONS, FieldType(field_type=np.uint32)),
        AnswerFieldDef(EFieldName.CURRENT_USAGE, FieldType(field_type=np.uint32)),
        AnswerFieldDef(EFieldName.CURRENT_WASTED, FieldType(field_type=np.uint32)),
        AnswerFieldDef(EFieldName.WATERMARK_ALLOCATIONS, FieldType(field_type=np.uint32)),
        AnswerFieldDef(EFieldName.WATERMARK_USAGE, FieldType(field_type=np.uint32)),
        AnswerFieldDef(EFieldName.WATERMARK_WASTED, FieldType(field_type=np.uint32))
    ]),
    user_manual_attrs=UserManualAttrs(
        description="Retrieves the allocator stats (size, num_allocations, usage, wasted) for a given allocator."
    ),
    is_release=False,
    group_id=GROUPS.logging,
    tags=["log", "performance"]
)

get_stack_usage = CommandContract(
    code=CommandCode.GET_STACK_USAGE,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(string_identifier="?stack_usage"),
        index_param=CommandParamDef(
            name=EFieldName.INDEX,
            param_type=FieldType(field_type=np.uint8, min_value=np.uint8(0)),
            user_manual_attrs=UserManualAttrs("Not used at the moment. But maybe in the future, for getting information about stacks of multiple cores")
        )
    ),
    answer_def=AnswerDef([
        AnswerFieldDef(EFieldName.SIZE, FieldType(field_type=np.uint32)),
        AnswerFieldDef(EFieldName.CURRENT_USAGE, FieldType(field_type=np.uint32)),
        AnswerFieldDef(EFieldName.WATERMARK_USAGE, FieldType(field_type=np.uint32)),
    ]),
    user_manual_attrs=UserManualAttrs(
        description="Retrieves usage stats for the stack of core0"
    ),
    is_release=False,
    group_id=GROUPS.logging,
    tags=["log", "performance"]
)

get_alloc_histogram_num_bins = CommandContract(
    code=CommandCode.GET_ALLOC_HISTOGRAM_NUM_BINS,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(string_identifier="?alloc_hist_num_bins")
    ),
    answer_def=AnswerDef([
        AnswerFieldDef(EFieldName.COUNT, field_type=FieldType(field_type=np.uint8))
    ]),
    user_manual_attrs=UserManualAttrs(
        description="Retrieves the number of bins in the allocation histogram"
    ),
    is_release=False,
    group_id=GROUPS.logging,
    tags=["log", "performance"]
)

get_alloc_histogram_bin = CommandContract(
    code=CommandCode.GET_ALLOC_HISTOGRAM_BIN,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(string_identifier="?alloc_hist_bin"),
        index_param=p.param_index_uint8
    ),
    answer_def=AnswerDef([
        AnswerFieldDef(EFieldName.VALUE, FieldType(field_type=np.uint32)),
        AnswerFieldDef(EFieldName.LIMIT, FieldType(field_type=np.uint32), UserManualAttrs("the upper bound of the bin")),
        AnswerFieldDef(EFieldName.SIZE, FieldType(field_type=np.uint32), UserManualAttrs("the length of the bin")),
    ]),
    is_release=False,
    group_id=GROUPS.logging,
    tags=["log", "performance"]
)
