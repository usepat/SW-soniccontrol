import asyncio
from typing import Type

import attrs
from attrs import validators

from sonic_protocol.python_parser import commands
from soniccontrol.interfaces import Scriptable
from soniccontrol.procedures.holder import HolderArgs, convert_to_holder_args
from soniccontrol.procedures.procedure import Procedure


@attrs.define(auto_attribs=True)
class AutoArgs:
    Scanning_f_center_Hz: int = attrs.field(validator=[
        validators.instance_of(int),
        validators.ge(100000),
        validators.le(10000000)
    ])
    Scanning_gain: int = attrs.field(validator=[
        validators.instance_of(int),
        validators.ge(0),
        validators.le(150)
    ])
    Scanning_f_range_Hz: int = attrs.field(validator=[
        validators.instance_of(int),
        validators.ge(0),
        validators.le(5000000)
    ])
    Scanning_f_step_Hz: int = attrs.field(validator=[
        validators.instance_of(int),
        validators.ge(0),
        validators.le(5000000)
    ])
    Scanning_t_step_ms: HolderArgs = attrs.field(
        default=HolderArgs(100, "ms"), 
        converter=convert_to_holder_args
    )
    Tuning_f_step_Hz: int = attrs.field(
        default=1000,
        validator=[
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


class AutoProc(Procedure):
    @classmethod
    def get_args_class(cls) -> Type: 
        return AutoArgs
    
    @property
    def is_remote(self) -> bool:
        return True

    async def execute(self, device: Scriptable, args: AutoArgs) -> None:
        await device.execute_command(commands.SetFrequency(args.Scanning_f_center_Hz))
        await device.execute_command(f"!scan_gain={args.Scanning_gain}")
        await device.execute_command(f"!scan_f_range={args.Scanning_f_range_Hz}")
        await device.execute_command(f"!scan_f_step={args.Scanning_f_step_Hz}")
        await device.execute_command(f"!scan_t_step={int(args.Scanning_t_step_ms.duration_in_ms)}")
        await device.execute_command(f"!tune_f_step={args.Tuning_f_step_Hz}")
        await device.execute_command(f"!tune_t_time={int(args.Tuning_time_ms.duration_in_ms)}")
        await device.execute_command(f"!tune_t_step={int(args.Tuning_t_step_ms.duration_in_ms)}")
        await device.execute_command("!auto")
