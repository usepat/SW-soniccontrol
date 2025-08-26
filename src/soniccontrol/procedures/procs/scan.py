import asyncio
from typing import Any, Type

import attrs
from attrs import fields, validators

from sonic_protocol.field_names import EFieldName
from sonic_protocol.python_parser import commands
from sonic_protocol.schema import SIPrefix, Version
from soniccontrol.procedures.holder import HolderArgs, convert_to_holder_args
from soniccontrol.procedures.procedure import Procedure, ProcedureArgs, custom_validator_factory
from sonic_protocol.command_codes import CommandCode
from soniccontrol.sonic_device import CommandExecutionError, CommandValidationError, SonicDevice
from soniccontrol_gui.utils.si_unit import AbsoluteFrequencySIVar, GainSIVar, RelativeFrequencySIVar


@attrs.define(auto_attribs=True)
class ScanArgs(ProcedureArgs):
    @classmethod
    def get_description(cls) -> str:
        return """The SCAN procedure measures the electric response of the connected add-on over
a wide frequency range at low gain and determines the optimal driving frequency.
"""

    f_center: AbsoluteFrequencySIVar = attrs.field(
        default=AbsoluteFrequencySIVar(1, SIPrefix.MEGA),
        metadata={"enum": EFieldName.SCAN_F_CENTER},
        # Is validated via SIMeta
    )
    gain: GainSIVar = attrs.field(
        default=GainSIVar(20),
        metadata={"enum": EFieldName.SCAN_GAIN},
    )
    f_range: RelativeFrequencySIVar = attrs.field(
        default=RelativeFrequencySIVar(8, SIPrefix.KILO),
        metadata={"enum": EFieldName.SCAN_F_RANGE},
    )
    f_step: RelativeFrequencySIVar = attrs.field(
        default=RelativeFrequencySIVar(1, SIPrefix.KILO),
        metadata={"enum": EFieldName.SCAN_F_STEP},
    )
    f_shift: RelativeFrequencySIVar = attrs.field(
        default=RelativeFrequencySIVar(0),
        metadata={"enum": EFieldName.SCAN_F_SHIFT},
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
        await device.execute_command(commands.SetFrequency(args.f_center.to_prefix(SIPrefix.NONE)))
        await device.execute_command(commands.SetScanFShift(args.f_shift.to_prefix(SIPrefix.NONE)))
        await device.execute_command(commands.SetScanGain(args.gain.to_prefix(SIPrefix.NONE)))
        await device.execute_command(commands.SetScanFRange(args.f_range.to_prefix(SIPrefix.NONE)))
        await device.execute_command(commands.SetScanFStep(args.f_step.to_prefix(SIPrefix.NONE)))
        t_step = int(args.t_step.duration_in_ms) if isinstance(args.t_step, HolderArgs) else int(args.t_step[0])
        await device.execute_command(commands.SetScanTStep(t_step))
        if not configure_only:
            await device.execute_command(commands.SetScan())

    async def fetch_args(self, device: SonicDevice) -> dict[str, Any]:
        try:
            answer = await device.execute_command(commands.GetScan(), raise_exception=False)
            answer_freq = await device.execute_command(commands.GetFreq(), raise_exception=False)
        except (CommandValidationError, CommandExecutionError) as _:
            return {}
        args = ScanArgs.from_answer(answer)
        if device._info.protocol_version < Version(2, 0, 0):
                f_center = answer_freq.field_value_dict.get(EFieldName.FREQUENCY, None)
                if f_center:
                    args.f_center = AbsoluteFrequencySIVar(f_center)
        # Returns nested dicts for the form widget
        return args.to_dict()
