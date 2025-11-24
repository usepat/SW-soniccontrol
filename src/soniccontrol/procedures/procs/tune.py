import asyncio
from typing import Any, Type

import attrs
from attrs import validators

from sonic_protocol.command_codes import CommandCode
from sonic_protocol.field_names import EFieldName
from sonic_protocol.python_parser import commands
from sonic_protocol.schema import SIPrefix
from soniccontrol.procedures.holder import HolderArgs, convert_to_holder_args
from soniccontrol.procedures.procedure import Procedure, ProcedureArgs
from soniccontrol.sonic_device import CommandExecutionError, CommandValidationError, SonicDevice
from sonic_protocol.si_unit import GainSIVar, RelativeFrequencySIVar


@attrs.define(auto_attribs=True)
class TuneArgs(ProcedureArgs):
    @classmethod
    def get_description(cls) -> str:
        return """The TUNE procedure is designed to tune the driving frequency to create the optimal field for the intended application.
It is helpful when certain parameters are expected to change significantly, e.g. temperature, liquid composition etc.
"""

    f_step: RelativeFrequencySIVar = attrs.field(
        default=RelativeFrequencySIVar(1, SIPrefix.KILO),
        metadata={"enum": EFieldName.TUNE_F_STEP},
    )
    t_time: HolderArgs = attrs.field(
        default=HolderArgs(5000, "ms"), 
        converter=convert_to_holder_args,
        metadata={"enum": EFieldName.TUNE_T_TIME}
    )

    n_steps: int = attrs.field(
        default=3,
        validator=[
            validators.instance_of(int),
            validators.ge(0)
        ],
        metadata={"enum": EFieldName.TUNE_N_STEPS}
    )
    f_shift: RelativeFrequencySIVar = attrs.field(
        default=RelativeFrequencySIVar(0),
        metadata={"enum": EFieldName.TUNE_F_SHIFT},
    )

    t_step: HolderArgs = attrs.field(
        default=HolderArgs(100, "ms"), 
        converter=convert_to_holder_args,
        metadata={"enum": EFieldName.TUNE_T_STEP}
    )
    gain: GainSIVar = attrs.field(
        default=GainSIVar(80),
        metadata={"enum": EFieldName.TUNE_GAIN},
    )

class TuneProc(Procedure):
    @classmethod
    def get_args_class(cls) -> Type: 
        return TuneArgs

    @property
    def is_remote(self) -> bool:
        return True

    async def execute(self, device: SonicDevice, args: TuneArgs, configure_only: bool = False) -> None:
        await device.execute_command(commands.SetTuneFShift(args.f_shift.to_prefix(SIPrefix.NONE)))
        await device.execute_command(commands.SetTuneNSteps(args.n_steps))
        await device.execute_command(commands.SetTuneFStep(args.f_step.to_prefix(SIPrefix.NONE)))
        t_time_duration = int(args.t_time.duration_in_ms) if isinstance(args.t_time, HolderArgs) else int(args.t_time[0])
        t_step_duration = int(args.t_step.duration_in_ms) if isinstance(args.t_step, HolderArgs) else int(args.t_step[0])

        await device.execute_command(commands.SetTuneTTime(t_time_duration))
        await device.execute_command(commands.SetTuneTStep(t_step_duration))
        if device.has_command(commands.SetTuneGain(args.gain.to_prefix(SIPrefix.NONE))):
            await device.execute_command(commands.SetTuneGain(args.gain.to_prefix(SIPrefix.NONE)))
        else:
            await device.execute_command(commands.SetGain(args.gain.to_prefix(SIPrefix.NONE)))
        
        if not configure_only:
            await device.execute_command(commands.SetTune())


    async def fetch_args(self, device: SonicDevice) -> dict[str, Any]:
        try:
            answer = await device.execute_command(commands.GetTune(), raise_exception=False)
        except (CommandValidationError, CommandExecutionError) as _:
            return {}
        args = TuneArgs.from_answer(answer)
        # Returns nested dicts for the form widget
        return args.to_dict()
