from typing import Any, Dict, List, Type, Union

import attrs
from attrs import validators

from sonic_protocol.field_names import EFieldName
from sonic_protocol.schema import SIPrefix
from soniccontrol.procedures.holder import Holder, HolderArgs, convert_to_holder_args
from soniccontrol.procedures.procedure import Procedure, ProcedureArgs, custom_validator_factory
from sonic_protocol.python_parser import commands
from soniccontrol.sonic_device import CommandExecutionError, CommandValidationError, SonicDevice
from soniccontrol_gui.utils.si_unit import AbsoluteFrequencySIVar, RelativeFrequencySIVar


@attrs.define(auto_attribs=True)
class RamperArgs(ProcedureArgs):
    @classmethod
    def get_description(cls) -> str:
        return """Ramp is a procedure that runs on the device. 
It starts at a start frequency f_start and steps through frequencies in increments of f_step, 
until it reaches the end frequency f_stop. 
The duration for which the signal is turned on is determined by t_on,
and the duration it remains off is determined by t_off. 
You can set t_off to 0 if you want the signal to never be turned off."""

    f_start: AbsoluteFrequencySIVar = attrs.field(
        default=AbsoluteFrequencySIVar(1, SIPrefix.MEGA),
        metadata={"enum": EFieldName.RAMP_F_START},
    )
    f_stop: AbsoluteFrequencySIVar = attrs.field(
        default=AbsoluteFrequencySIVar(2, SIPrefix.MEGA),
        metadata={"enum": EFieldName.RAMP_F_STOP},
    )
    f_step: RelativeFrequencySIVar = attrs.field(
        default=RelativeFrequencySIVar(100, SIPrefix.KILO),
        metadata={"enum": EFieldName.RAMP_F_STEP},
        validator=custom_validator_factory(RelativeFrequencySIVar, RelativeFrequencySIVar(10), RelativeFrequencySIVar(5, SIPrefix.MEGA))
    )

    t_on: HolderArgs = attrs.field(
        default=HolderArgs(500, "ms"),
        converter=convert_to_holder_args,
        metadata={"enum": EFieldName.RAMP_T_ON}
    )
    t_off: HolderArgs = attrs.field(
        default=HolderArgs(0, "ms"),
        converter=convert_to_holder_args,
        metadata={"enum": EFieldName.RAMP_T_OFF}
    )


class Ramper(Procedure):
    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def get_args_class(cls) -> Type:
        return RamperArgs


class RamperLocal(Ramper):
    def __init__(self) -> None:
        super().__init__()

    async def execute(
        self,
        device: SonicDevice,
        args: RamperArgs
    ) -> None:
        values = [args.f_start.to_prefix(SIPrefix.NONE) + i * args.f_step.to_prefix(SIPrefix.NONE) for i in range(int((args.f_stop.to_prefix(SIPrefix.NONE) - args.f_start.to_prefix(SIPrefix.NONE)) / args.f_step.to_prefix(SIPrefix.NONE)) + 1) ]

        # await device.get_overview() # FIXME I dont think we need this
        # I am removing it for now because we can't send commands to the crystal device that have no command code
        # TODO: Do we need those two lines?
        # await device.execute_command(f"!freq={start}")
        # await device.set_signal_on()
        await self._ramp(device, list(values), args.t_on, args.t_off)
    
        await device.set_signal_off()

    @property
    def is_remote(self) -> bool:
        return False

    async def _ramp(
        self,
        device: SonicDevice,
        values: List[Union[int, float]],
        hold_on: HolderArgs,
        hold_off: HolderArgs,
    ) -> None:
        i: int = 0
        await device.set_signal_on()
        while i < len(values):
            value = values[i]

            await device.execute_command(commands.SetFrequency(int(value))) 
            if hold_off.duration:
                await device.set_signal_on()
            await Holder.execute(hold_on)

            if hold_off.duration:
                await device.set_signal_off()
                await Holder.execute(hold_off)

            i += 1

    async def fetch_args(self, device: SonicDevice) -> Dict[str, Any]:
        return {}


class RamperRemote(Ramper):
    def __init__(self) -> None:
        super().__init__()

    @property
    def is_remote(self) -> bool:
        return True

    async def execute(
        self,
        device: SonicDevice,
        args: RamperArgs,
        configure_only: bool = False,
    ) -> None:
        await device.execute_command(commands.SetRampFStart(args.f_start.to_prefix(SIPrefix.NONE)))
        await device.execute_command(commands.SetRampFStop(args.f_stop.to_prefix(SIPrefix.NONE)))
        await device.execute_command(commands.SetRampFStep(args.f_step.to_prefix(SIPrefix.NONE)))
        # When the args are retrieved from the Form Widget, the HolderArgs are tuples instead
        t_on_duration = int(args.t_on.duration_in_ms)
        t_off_duration = int(args.t_off.duration_in_ms)

        await device.execute_command(commands.SetRampTOn(t_on_duration))
        await device.execute_command(commands.SetRampTOff(t_off_duration))

        if not configure_only:
            await device.execute_command(commands.SetRamp())

    async def fetch_args(self, device: SonicDevice) -> Dict[str, Any]:
        try:
            answer = await device.execute_command(commands.GetRamp(), raise_exception=False)
        except (CommandValidationError, CommandExecutionError) as _:
            return {}
        args = RamperArgs.from_answer(answer)
        # Returns nested dicts for the form widget
        return args.to_dict()
