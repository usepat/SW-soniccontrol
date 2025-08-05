import asyncio
from typing import Any, Type

import attrs
from attrs import fields, validators

from sonic_protocol.field_names import EFieldName
from sonic_protocol.python_parser import commands
from sonic_protocol.schema import Version
from soniccontrol.procedures.holder import HolderArgs, convert_to_holder_args
from soniccontrol.procedures.procedure import Procedure, ProcedureArgs
from sonic_protocol.command_codes import CommandCode
from soniccontrol.sonic_device import SonicDevice


@attrs.define(auto_attribs=True)
class ScanArgs(ProcedureArgs):
    @classmethod
    def get_description(cls) -> str:
        return """The SCAN procedure measures the electric response of the connected add-on over
a wide frequency range at low gain and determines the optimal driving frequency.
"""
    
    f_center: int = attrs.field(
        default=1000000,
        validator=[
            validators.instance_of(int),
            validators.ge(100000),
            validators.le(10000000),
        ],
        metadata={"enum": EFieldName.SCAN_F_CENTER}
    )
    gain: int = attrs.field(
        default=20,
        validator=[
            validators.instance_of(int),
            validators.ge(0),
            validators.le(150)
        ],
        metadata={"enum": EFieldName.SCAN_GAIN}
    )
    f_range: int = attrs.field(
        default=8000,
        validator=[
            validators.instance_of(int),
            validators.ge(0),
            validators.le(5000000)
        ],
        metadata={"enum": EFieldName.SCAN_F_RANGE}
    )
    f_step: int = attrs.field(
        default=1000,
        validator=[
            validators.instance_of(int),
            validators.ge(0),
            validators.le(5000000)
        ],
        metadata={"enum": EFieldName.SCAN_F_STEP}
    )

    f_shift: int = attrs.field(
        default=0,
        validator=[
            validators.instance_of(int),
            validators.ge(0),
            validators.le(5000000)
        ],
        metadata={"enum": EFieldName.SCAN_F_SHIFT}
    )

    t_step: HolderArgs = attrs.field(
        default=HolderArgs(100, "ms"), 
        converter=convert_to_holder_args,
        metadata={"enum": EFieldName.SCAN_T_STEP}
    )

class ScanProc(Procedure):
    @classmethod
    def get_args_class(cls) -> Type: 
        return ScanArgs

    @property
    def is_remote(self) -> bool:
        return True

    async def execute(self, device: SonicDevice, args: ScanArgs, configure_only: bool = False) -> None:
        await device.execute_command(commands.SetFrequency(args.f_center))
        await device.execute_command(commands.SetScanFShift(args.f_shift))
        await device.execute_command(commands.SetScanGain(args.gain))
        await device.execute_command(commands.SetScanFRange(args.f_range))
        await device.execute_command(commands.SetScanFStep(args.f_step))
        t_step = int(args.t_step.duration_in_ms) if isinstance(args.t_step, HolderArgs) else int(args.t_step[0])
        await device.execute_command(commands.SetScanTStep(t_step))
        if not configure_only:
            await device.execute_command(commands.SetScan())

    async def fetch_args(self, device: SonicDevice) -> dict[str, Any]:
        answer = await device.execute_command(commands.GetScan(), raise_exception=False)
        answer_freq = await device.execute_command(commands.GetFreq(), raise_exception=False)

        arg_dict = {}
        if answer.was_validated and answer.valid:
            # TODO in next protocol version return scan_f_center and scan_gain in getScan
            arg_dict.update(ScanArgs.to_dict_with_holder_args(answer))
            if device._info.protocol_version < Version(2, 0, 0):
                arg_dict[EFieldName.SCAN_F_CENTER] = answer_freq.field_value_dict.get(EFieldName.FREQUENCY)
        return arg_dict