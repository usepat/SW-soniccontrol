import asyncio
from typing import Any, Type

import attrs
from attrs import validators

from sonic_protocol.command_codes import CommandCode
from sonic_protocol.field_names import EFieldName
from sonic_protocol.python_parser import commands
from soniccontrol.interfaces import Scriptable
from soniccontrol.procedures.holder import HolderArgs, convert_to_holder_args
from soniccontrol.procedures.procedure import Procedure


@attrs.define(auto_attribs=True)
class TuneArgs:
    tune_f_step: int = attrs.field(
        default=1000,
        validator=[
        validators.instance_of(int),
        validators.ge(0),
        validators.le(5000000)
    ])
    tune_t_time: HolderArgs = attrs.field(
        default=HolderArgs(100, "ms"), 
        converter=convert_to_holder_args
    )

    tune_t_step: HolderArgs = attrs.field(
        default=HolderArgs(100, "ms"), 
        converter=convert_to_holder_args
    )

class TuneProc(Procedure):
    @classmethod
    def get_args_class(cls) -> Type: 
        return TuneArgs

    @property
    def is_remote(self) -> bool:
        return True

    async def execute(self, device: Scriptable, args: TuneArgs) -> None:
        await device.execute_command(commands.SetTuneFStep(args.tune_f_step))
        await device.execute_command(commands.SetTuneTTime(int(args.tune_t_time.duration_in_ms)))
        await device.execute_command(commands.SetTuneTStep(int(args.tune_t_step.duration_in_ms)))
        await device.execute_command(commands.SetTune())

    async def fetch_args(self, device: Scriptable) -> dict[str, Any]:
        answer = await device.execute_command(commands.GetTune())
        if answer.was_validated and answer.valid:
            return {
                "tune_f_step": answer.field_value_dict.get(EFieldName.TUNE_F_STEP, 0),
                "tune_t_time":  HolderArgs(float(answer.field_value_dict.get(EFieldName.TUNE_T_TIME, 0)), "ms"),
                "tune_t_step": HolderArgs(float(answer.field_value_dict.get(EFieldName.TUNE_T_STEP, 0)), "ms"),
            }
        return {}
