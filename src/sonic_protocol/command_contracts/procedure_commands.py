

from typing import List
from sonic_protocol.command_codes import CommandCode
from sonic_protocol.defs import AnswerDef, AnswerFieldDef, CommandContract, CommandDef, CommandParamDef, FieldType, SonicTextCommandAttrs, UserManualAttrs
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
                                           field_type = FieldType(field_type=int), response_field: AnswerFieldDef | None = None, release: bool = True) -> CommandContract:
    
    procedure_name = command_code.name.split("_")[1] # This is a hack. I am lazy
    if response_field is None:
        assert (field_name is not None)
        response_field = AnswerFieldDef(
            field_name=field_name,
            field_type=field_type
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

ramp_proc_commands: List[CommandContract] = [
    generate_start_procedure_contract(
        CommandCode.SET_RAMP,
        ["!ramp", "start_ramp"],
        ""
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_RAMP_F_START, 
    ["!ramp_f_start"], 
    EFieldName.RAMP_F_START, 
    ""
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_RAMP_F_STOP, 
    ["!ramp_f_stop"], 
    EFieldName.RAMP_F_STOP, 
    ""
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_RAMP_F_STEP, 
    ["!ramp_f_step"], 
    EFieldName.RAMP_F_STEP, 
    ""
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_RAMP_T_ON, 
    ["!ramp_t_on"], 
    EFieldName.RAMP_T_ON, 
    ""
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_RAMP_T_OFF, 
    ["!ramp_t_off"], 
    EFieldName.RAMP_T_OFF, 
    ""
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
    description=""
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_SCAN_F_RANGE, 
    ["!scan_f_range"], 
    response_field=fields.field_scan_f_half_range,
    description=""
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_SCAN_T_STEP, 
    ["!scan_t_step"], 
    response_field=fields.field_scan_t_step,
    description=""
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
    description=""
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_TUNE_T_STEP, 
    ["!tune_t_step"], 
    EFieldName.TUNE_T_STEP,
    description=""
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_TUNE_T_TIME, 
    ["!tune_t_time"], 
    response_field=fields.field_tune_t_time,
    description=""
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
    description=""
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_WIPE_F_RANGE, 
    ["!wipe_f_range"], 
    response_field=fields.field_wipe_f_range,
    description=""
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_WIPE_F_RANGE, 
    ["!wipe_f_range"], 
    response_field=fields.field_wipe_f_range,
    description=""
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_WIPE_T_ON, 
    ["!wipe_t_on"], 
    response_field=fields.field_wipe_t_on,
    description=""
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_WIPE_T_OFF, 
    ["!wipe_t_off"], 
    response_field=fields.field_wipe_t_off,
    description=""
    ),
    generate_procedure_arg_setter_contract(
    CommandCode.SET_WIPE_T_PAUSE, 
    ["!wipe_t_pause"], 
    response_field=fields.field_wipe_t_pause,
    description=""
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
        EFieldName.TIMING,
        ""
    ),
    generate_procedure_arg_setter_contract(
        CommandCode.SET_DUTY_CYCLE_T_ON,
        ["!duty_cycle_t_on"],
        EFieldName.TIMING,
        ""
    ),
]


all_proc_commands = ramp_proc_commands + wipe_proc_commands + scan_proc_commands + tune_proc_commands + auto_proc_commands + duty_cycle_proc_commands