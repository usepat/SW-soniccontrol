import asyncio
from typing import Any, Type

import attrs
from attrs import validators

from sonic_protocol.field_names import EFieldName
from sonic_protocol.python_parser import commands
from soniccontrol.interfaces import Scriptable
from soniccontrol.procedures.holder import HolderArgs, convert_to_holder_args
from soniccontrol.procedures.procedure import Procedure
from sonic_protocol.command_codes import CommandCode


@attrs.define(auto_attribs=True)
class ScanArgs:
    scan_f_center: int = attrs.field(validator=[
        validators.instance_of(int),
        validators.ge(100000),
        validators.le(10000000)
    ])
    scan_gain: int = attrs.field(validator=[
        validators.instance_of(int),
        validators.ge(0),
        validators.le(150)
    ])
    scan_f_range: int = attrs.field(validator=[
        validators.instance_of(int),
        validators.ge(0),
        validators.le(5000000)
    ])
    scan_f_step: int = attrs.field(validator=[
        validators.instance_of(int),
        validators.ge(0),
        validators.le(5000000)
    ])
    scan_t_step: HolderArgs = attrs.field(
        default=HolderArgs(100, "ms"), 
        converter=convert_to_holder_args
    )

class ScanProc(Procedure):
    @classmethod
    def get_args_class(cls) -> Type: 
        return ScanArgs

    @property
    def is_remote(self) -> bool:
        return True

    async def execute(self, device: Scriptable, args: ScanArgs) -> None:
        await device.execute_command(commands.SetFrequency(args.scan_f_center))
        await device.execute_command(commands.SetScanGain(args.scan_gain))
        await device.execute_command(commands.SetScanFRange(args.scan_f_range))
        await device.execute_command(commands.SetScanFStep(args.scan_f_step))
        await device.execute_command(commands.SetScanTStep(int(args.scan_t_step.duration_in_ms)))
        await device.execute_command(commands.SetScan())

    async def fetch_args(self, device: Scriptable) -> dict[str, Any]:
        answer = await device.execute_command(commands.GetScan())
        answer_freq = await device.execute_command(commands.GetFreq())
        if answer.was_validated and answer.valid and answer_freq.was_validated and answer_freq.valid:
            return {
                "scan_f_center": answer_freq.field_value_dict.get(EFieldName.FREQUENCY, 0),
                "scan_f_range": answer.field_value_dict.get(EFieldName.SCAN_F_RANGE, 0),
                "scan_f_step": answer.field_value_dict.get(EFieldName.SCAN_F_STEP, 0),
                "scan_t_step": HolderArgs(float(answer.field_value_dict.get(EFieldName.SCAN_T_STEP, 0)), "ms"),
            }
        return {}