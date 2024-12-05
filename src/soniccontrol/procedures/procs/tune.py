import asyncio
from typing import Type

import attrs
from attrs import validators

from soniccontrol.interfaces import Scriptable
from soniccontrol.procedures.holder import HolderArgs, convert_to_holder_args
from soniccontrol.procedures.procedure import Procedure


@attrs.define(auto_attribs=True)
class TuneArgs:
    Tuning_f_step_Hz: int = attrs.field(validator=[
        validators.instance_of(int),
        validators.ge(0),
        validators.le(5000000)
    ])
    Tuning_time_ms: HolderArgs = attrs.field(
        default=HolderArgs(100, "ms"), 
        converter=convert_to_holder_args
    )

    Tuning_t_step_ms: HolderArgs = attrs.field(
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
        await device.execute_command(f"!tune_f_step={args.Tuning_f_step_Hz}")
        await device.execute_command(f"!tune_t_time={int(args.Tuning_time_ms.duration_in_ms)}")
        await device.execute_command(f"!tune_t_step={int(args.Tuning_t_step_ms.duration_in_ms)}")
        await device.execute_command("!tune")

