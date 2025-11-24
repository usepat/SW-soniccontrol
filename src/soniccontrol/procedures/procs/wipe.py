from typing import Any, Type

import attrs
from attrs import validators

from sonic_protocol.field_names import EFieldName
from sonic_protocol.python_parser import commands
from sonic_protocol.schema import SIPrefix
from soniccontrol.procedures.holder import HolderArgs, convert_to_holder_args
from soniccontrol.procedures.procedure import Procedure, ProcedureArgs, custom_validator_factory
from sonic_protocol.command_codes import CommandCode
from soniccontrol.sonic_device import CommandExecutionError, CommandValidationError, SonicDevice
from sonic_protocol.si_unit import AbsoluteFrequencySIVar, RelativeFrequencySIVar, GainSIVar


@attrs.define(auto_attribs=True)
class WipeArgs(ProcedureArgs):
    @classmethod
    def get_description(cls) -> str:
        return """The WIPE procedure is designed for driving our ultrasonic add-ons for cleaning 
(or keeping clean) various inline probes directly in the process.
It is a special protocol optimized to enhance the cleaning effect of ultrasound, whilst not creating hard cavitation to keep probe integrity.
"""     

    f_range: RelativeFrequencySIVar = attrs.field(
        default=RelativeFrequencySIVar(value=8000),
        metadata={"enum": EFieldName.WIPE_F_RANGE},
    )
    f_step: RelativeFrequencySIVar = attrs.field(
        default=RelativeFrequencySIVar(10),
        metadata={"enum": EFieldName.WIPE_F_STEP},
        validator=custom_validator_factory(RelativeFrequencySIVar, RelativeFrequencySIVar(10), RelativeFrequencySIVar(5, SIPrefix.MEGA))
    )
    t_on: HolderArgs = attrs.field(
        default=HolderArgs(500, "ms"), 
        metadata={"enum": EFieldName.WIPE_T_ON},
        converter=convert_to_holder_args
    )
    t_off: HolderArgs = attrs.field(
        default=HolderArgs(20, "ms"), 
        metadata={"enum": EFieldName.WIPE_T_OFF},
        converter=convert_to_holder_args
    )
    t_pause: HolderArgs = attrs.field(
        default=HolderArgs(2000, "ms"),
        metadata={"enum": EFieldName.WIPE_T_PAUSE},
        converter=convert_to_holder_args
    )
    gain: GainSIVar = attrs.field(
        default=GainSIVar(150),
        metadata={"enum": EFieldName.WIPE_GAIN},
    )

class WipeProc(Procedure):    
    @classmethod
    def get_args_class(cls) -> Type: 
        return WipeArgs

    @property
    def is_remote(self) -> bool:
        return True

    async def execute(self, device: SonicDevice, args: WipeArgs, configure_only: bool = False) -> None:
        self.f_step = RelativeFrequencySIVar(0) 
        await device.execute_command(commands.SetWipeFRange(args.f_range.to_prefix(SIPrefix.NONE)))
        await device.execute_command(commands.SetWipeFStep(args.f_step.to_prefix(SIPrefix.NONE)))
        t_on_duration = int(args.t_on.duration_in_ms) if isinstance(args.t_on, HolderArgs) else int(args.t_on[0])
        t_off_duration = int(args.t_off.duration_in_ms) if isinstance(args.t_off, HolderArgs) else int(args.t_off[0])
        t_pause_duration = int(args.t_pause.duration_in_ms) if isinstance(args.t_pause, HolderArgs) else int(args.t_pause[0])

        await device.execute_command(commands.SetWipeTOn(t_on_duration))
        await device.execute_command(commands.SetWipeTOff(t_off_duration))
        await device.execute_command(commands.SetWipeTPause(t_pause_duration))
        if device.has_command(commands.SetWipeGain(args.gain.to_prefix(SIPrefix.NONE))):
            await device.execute_command(commands.SetWipeGain(args.gain.to_prefix(SIPrefix.NONE)))
        else:
            await device.execute_command(commands.SetGain(args.gain.to_prefix(SIPrefix.NONE)))

        if not configure_only:
            await device.execute_command(commands.SetWipe())

    async def fetch_args(self, device: SonicDevice) -> dict[str, Any]:
        try:
            answer = await device.execute_command(commands.GetWipe(), raise_exception=False)
        except (CommandValidationError, CommandExecutionError) as _:
            return {}
        args = WipeArgs.from_answer(answer)
        # Returns nested dicts for the form widget
        return args.to_dict()