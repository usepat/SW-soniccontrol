

from typing import List
from sonic_protocol.command_codes import CommandCode
from sonic_protocol.defs import AnswerDef, AnswerFieldDef, CommandContract, CommandDef, CommandParamDef, DeviceParamConstantType, FieldType, SonicTextCommandAttrs, UserManualAttrs
from sonic_protocol.field_names import EFieldName
import sonic_protocol.command_contracts.fields as fields


def generate_start_procedure_contract(command_code: CommandCode, string_identifiers: List[str], description: str | None = None, release: bool = True) -> CommandContract:
    procedure_name = "".join(command_code.name.split("_")[1:]) # This is a hack. I am lazy
    return CommandContract(
        code=command_code,
        command_defs=CommandDef(
            sonic_text_attrs=SonicTextCommandAttrs(
                string_identifier=string_identifiers
            )
        ),
        answer_defs=AnswerDef(
            fields=[fields.field_procedure]
        ),
        user_manual_attrs=UserManualAttrs(
            description=description
        ),
        is_release=release,
        tags=["Procedure", procedure_name]
    )


def generate_procedure_arg_setter_contract(command_code: CommandCode, string_identifiers: List[str], 
                                           field_name: EFieldName | None = None, description: str | None = None, 
                                           field_type = FieldType(field_type=int),
                                           response_field: AnswerFieldDef | None = None, release: bool = True) -> CommandContract:
    
    procedure_name = command_code.name.split("_")[1] # This is a hack. I am lazy
    if response_field is None:
        assert (field_name is not None)
        response_field = AnswerFieldDef(
            field_name=field_name,
            field_type=field_type,
        )
    return CommandContract(
        code=command_code,
        command_defs=CommandDef(
            setter_param=CommandParamDef(
                name=EFieldName.PROCEDURE_ARG,
                param_type=response_field.field_type
            ),
            sonic_text_attrs=SonicTextCommandAttrs(
                string_identifier=string_identifiers
            )
        ),
        is_release=release,
        answer_defs=AnswerDef(
            fields=[response_field]
        ),
        user_manual_attrs=UserManualAttrs(
            description=description
        ),
        tags=["Procedure", procedure_name]
    )

get_ramp = CommandContract(
    code=CommandCode.GET_RAMP,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?ramp"]
        )
    ), 
    is_release=True,
    answer_defs=AnswerDef(
        fields=[
            fields.field_ramp_f_start,
            fields.field_ramp_f_stop,
            fields.field_ramp_f_step,
            fields.field_ramp_t_on,
            fields.field_ramp_t_off
        ]
    ),
    tags=["Procedure", "RAMP"]
)

ramp_proc_commands: List[CommandContract] = [
    generate_start_procedure_contract(
        CommandCode.SET_RAMP,
        ["!ramp", "start_ramp"],
        ""
    ),
    get_ramp,
    generate_procedure_arg_setter_contract(
    CommandCode.SET_RAMP_F_START, 
    ["!ramp_f_start"],
    response_field=fields.field_ramp_f_start 
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_RAMP_F_STOP, 
    ["!ramp_f_stop"],
     response_field=fields.field_ramp_f_stop
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_RAMP_F_STEP, 
    ["!ramp_f_step"], 
    response_field=fields.field_ramp_f_step
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_RAMP_T_ON, 
    ["!ramp_t_on"], 
     response_field=fields.field_ramp_t_on
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_RAMP_T_OFF, 
    ["!ramp_t_off"], 
     response_field=fields.field_ramp_t_off
    )
]




get_auto = CommandContract(
    code=CommandCode.GET_AUTO,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?auto"]
        )
    ), 
    is_release=True,
    answer_defs=AnswerDef(
        fields=[
            fields.field_scan_f_step,
            fields.field_scan_f_half_range,
            fields.field_scan_t_step,
            fields.field_tune_f_step,
            fields.field_tune_t_time
        ]
    ),
    tags=["Procedure", "AUTO"]
)

auto_proc_commands: List[CommandContract] = [
    generate_start_procedure_contract(
        CommandCode.SET_AUTO,
        ["!auto"],
        ""
    ),
    get_auto
]

get_scan = CommandContract(
    code=CommandCode.GET_SCAN,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?scan"]
        )
    ), 
    is_release=True,
    answer_defs=AnswerDef(
        fields=[
            fields.field_scan_f_step,
            fields.field_scan_f_half_range,
            fields.field_scan_t_step,
        ]
    ),
    tags=["Procedure", "SCAN"]
)

scan_proc_commands: List[CommandContract] = [
    generate_start_procedure_contract(
        CommandCode.SET_SCAN,
        ["!scan"],
        description=""
    ),
    get_scan,
    generate_procedure_arg_setter_contract(
    CommandCode.SET_SCAN_F_STEP, 
    ["!scan_f_step"], 
    response_field=fields.field_scan_f_step, 
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_SCAN_F_RANGE, 
    ["!scan_f_range"], 
    response_field=fields.field_scan_f_half_range,
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_SCAN_T_STEP, 
    ["!scan_t_step"], 
    response_field=fields.field_scan_t_step,
    )
]

get_tune = CommandContract(
    code=CommandCode.GET_TUNE,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?tune"]
        )
    ), 
    is_release=True,
    answer_defs=AnswerDef(
        fields=[
            fields.field_tune_f_step,
            fields.field_tune_t_time
        ]
    ),
    tags=["Procedure", "TUNE"]
)

tune_proc_commands: List[CommandContract] = [
    generate_start_procedure_contract(
        CommandCode.GET_TUNE,
        ["!tune"],
        ""
    ),
    get_tune,
    generate_procedure_arg_setter_contract(
    CommandCode.SET_TUNE_F_STEP, 
    ["!tune_f_step"], 
    response_field=fields.field_tune_f_step,
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_TUNE_T_STEP, 
    ["!tune_t_step"], 
    response_field=fields.field_tune_t_step
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_TUNE_T_TIME, 
    ["!tune_t_time"], 
    response_field=fields.field_tune_t_time,
    )
]

get_wipe = CommandContract(
    code=CommandCode.GET_WIPE,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?wipe"]
        )
    ), 
    is_release=True,
    answer_defs=AnswerDef(
        fields=[
            fields.field_wipe_f_step,
            fields.field_wipe_f_range,
            fields.field_wipe_t_on,
            fields.field_wipe_t_off,
            fields.field_wipe_t_pause,
        ]
    ),
    tags=["Procedure", "WIPE"]
)

wipe_proc_commands: List[CommandContract] = [
    generate_start_procedure_contract(
        CommandCode.SET_WIPE,
        ["!wipe"],
        description=""
    ),
    get_wipe,
    generate_procedure_arg_setter_contract(
    CommandCode.SET_WIPE_F_STEP, 
    ["!wipe_f_step"], 
    response_field=fields.field_wipe_f_step, 
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_WIPE_F_RANGE, 
    ["!wipe_f_range"], 
    response_field=fields.field_wipe_f_range,
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_WIPE_F_RANGE, 
    ["!wipe_f_range"], 
    response_field=fields.field_wipe_f_range,
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_WIPE_T_ON, 
    ["!wipe_t_on"], 
    response_field=fields.field_wipe_t_on,
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_WIPE_T_OFF, 
    ["!wipe_t_off"], 
    response_field=fields.field_wipe_t_off,
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_WIPE_T_PAUSE, 
    ["!wipe_t_pause"], 
    response_field=fields.field_wipe_t_pause,
    )
]

get_duty_cycle = CommandContract(
    code=CommandCode.GET_DUTY_CYCLE,
    command_defs=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?duty_cycle"]
        )
    ), 
    is_release=True,
    answer_defs=AnswerDef(
        fields=[
            fields.field_duty_cycle_t_on,
            fields.field_duty_cycle_t_off
        ]
    ),
    tags=["Procedure", "DUTY_CYCLE"]
)


stop_command =  generate_start_procedure_contract(
    CommandCode.SET_STOP,
    ["!stop", "!stop_procedure"],
    ""
)
continue_command =  generate_start_procedure_contract(
    CommandCode.SET_CONTINUE,
    ["!continue", "!continue_procedure"],
    ""
)

duty_cycle_proc_commands: List[CommandContract] = [
    generate_start_procedure_contract(
        CommandCode.SET_DUTY_CYCLE,
        ["!duty_cycle"],
        description="Starts a duty cycle for defined behaviour"
    ),
    get_duty_cycle,
    generate_procedure_arg_setter_contract(
        CommandCode.SET_DUTY_CYCLE_T_OFF,
        ["!duty_cycle_t_off"],
        response_field=fields.field_duty_cycle_t_off
    ),
    generate_procedure_arg_setter_contract(
        CommandCode.SET_DUTY_CYCLE_T_ON,
        ["!duty_cycle_t_on"],
        response_field=fields.field_duty_cycle_t_on
    ),
    stop_command,
    continue_command
]





all_proc_commands = [stop_command, continue_command]
all_proc_commands.extend(ramp_proc_commands)
all_proc_commands.extend(wipe_proc_commands)
all_proc_commands.extend(scan_proc_commands)
all_proc_commands.extend(tune_proc_commands)
all_proc_commands.extend(auto_proc_commands)
all_proc_commands.extend(duty_cycle_proc_commands)
