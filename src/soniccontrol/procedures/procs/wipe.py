import asyncio
from typing import Type

import attrs
from attrs import validators

from soniccontrol.interfaces import Scriptable
from soniccontrol.procedures.holder import HolderArgs, convert_to_holder_args
from soniccontrol.procedures.procedure import Procedure


@attrs.define(auto_attribs=True)
class WipeArgs:
    Wipe_f_range_Hz: int = attrs.field(validator=[
        validators.instance_of(int),
        validators.ge(0),
        validators.le(5000000)
    ])
    Wipe_f_step_Hz: int = attrs.field(validator=[
        validators.instance_of(int),
        validators.ge(10),
        validators.le(5000000)
    ])
    Wipe_t_on_ms: HolderArgs = attrs.field(
        default=HolderArgs(100, "ms"), 
        converter=convert_to_holder_args
    )
    Wipe_t_off_ms: HolderArgs = attrs.field(
        default=HolderArgs(0, "ms"), 
        converter=convert_to_holder_args
    )
    Wipe_t_pause_ms: HolderArgs = attrs.field(
        default=HolderArgs(1000, "ms"), 
        converter=convert_to_holder_args
    )

class WipeProc(Procedure):
    @classmethod
    def get_args_class(cls) -> Type: 
        return WipeArgs

    @property
    def is_remote(self) -> bool:
        return True

    async def execute(self, device: Scriptable, args: WipeArgs) -> None:
        await device.execute_command(f"!wipe_f_range={args.Wipe_f_range_Hz}")
        await device.execute_command(f"!wipe_f_step={args.Wipe_f_step_Hz}")
        await device.execute_command(f"!wipe_t_on={int(args.Wipe_t_on_ms.duration_in_ms)}")
        await device.execute_command(f"!wipe_t_off={int(args.Wipe_t_off_ms.duration_in_ms)}")
        await device.execute_command(f"!wipe_t_pause={int(args.Wipe_t_pause_ms.duration_in_ms)}")
        await device.execute_command("!wipe")
