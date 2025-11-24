import asyncio
import attrs
from typing import Any, Dict, Tuple, Type
import click

from soniccontrol.procedures.holder import HolderArgs, convert_to_holder_args
from soniccontrol.procedures.procedure import ProcedureType
from soniccontrol.procedures.procs.auto import AutoArgs
from soniccontrol.procedures.procs.ramper import RamperArgs
from soniccontrol.procedures.procs.scan import ScanArgs
from soniccontrol.procedures.procs.tune import TuneArgs
from soniccontrol.procedures.procs.wipe import WipeArgs
from soniccontrol.remote_controller import RemoteController


class HolderParam(click.ParamType):
    name = "duration"

    def convert(self, value: Any, param: click.Parameter | None, ctx: click.Context | None) -> Any:
        try:
            return convert_to_holder_args(value)
        except ValueError as e:
            self.fail(str(e), param, ctx)
        except TypeError:
            self.fail(f"{value!r} could not be converted", param, ctx)

def create_click_option(arg_name: str, arg_type: attrs.Attribute):
    type_ = arg_type.type
    assert (type_)
    if issubclass(type_, HolderArgs):
        type_ = HolderParam()

    cmd_opt_name = "--" + arg_name.replace("_", "-")  
    return click.Option([cmd_opt_name], type=type_, prompt=arg_name)

def create_procedure_command(command_str: str, procedure_type: ProcedureType, 
                            proc_arg_class: Type) -> click.Command:
    @click.pass_context
    def callback(ctx: click.Context, **kwargs):
        remote_controller: RemoteController = ctx.obj["REMOTE_CONTROLLER"]
        async_loop: asyncio.AbstractEventLoop = ctx.obj["ASYNC_LOOP"]
        remote_controller.execute_procedure(procedure_type, kwargs, async_loop)
    
    return click.Command(
        name=command_str,
        callback=callback,
        params=[
            create_click_option(arg_name, arg_type)
            for arg_name, arg_type in attrs.fields_dict(proc_arg_class).items()
        ]
    )

def add_procedure_commands(group: click.Group):
    procedures: Dict[str, Tuple[ProcedureType, Type]] = {
        "auto": (ProcedureType.AUTO, AutoArgs),
        "ramp": (ProcedureType.RAMP, RamperArgs),
        "scan": (ProcedureType.SCAN, ScanArgs),
        "tune": (ProcedureType.TUNE, TuneArgs),
        "wipe": (ProcedureType.WIPE, WipeArgs),
    }

    for command_str, (procedure_type, proc_arg_class) in procedures.items():

        command = create_procedure_command(command_str, procedure_type, proc_arg_class)
        group.add_command(command)
