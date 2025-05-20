from typing import Any, Dict, List, Type, Union

import attrs
from attrs import validators

from sonic_protocol.field_names import EFieldName
from soniccontrol.interfaces import Scriptable
from soniccontrol.procedures.holder import Holder, HolderArgs, convert_to_holder_args
from soniccontrol.procedures.procedure import Procedure, ProcedureArgs
from sonic_protocol.python_parser import commands


@attrs.define(auto_attribs=True, init=False)
class RamperArgs(ProcedureArgs):
    @classmethod
    def get_description(cls) -> str:
        return """Ramp is a procedure that runs on the device. 
It starts at a start frequency f_start and steps through frequencies in increments of f_step, 
until it reaches the end frequency f_stop. 
The duration for which the signal is turned on is determined by t_on,
and the duration it remains off is determined by t_off. 
You can set t_off to 0 if you want the signal to never be turned off."""

    f_start: int = attrs.field(
        default=1000000,
        validator=[
            validators.instance_of(int),
            validators.ge(0),
            validators.le(10_000_000)
        ],
        metadata={"enum": EFieldName.RAMP_F_START}
    )
    f_stop: int = attrs.field(
        default=2000000,
        validator=[
            validators.instance_of(int),
            validators.ge(0),
            validators.le(10_000_000)
        ],
        metadata={"enum": EFieldName.RAMP_F_STOP}
    )
    f_step: int = attrs.field(
        default=100000,
        validator=[
            validators.instance_of(int),
            validators.ge(10),
            validators.le(500_000)
        ],
        metadata={"enum": EFieldName.RAMP_F_STEP}
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
        device: Scriptable,
        args: RamperArgs
    ) -> None:
        values = [args.f_start + i * args.f_step for i in range(int((args.f_stop - args.f_start) / args.f_step) + 1) ]

        await device.get_overview()
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
        device: Scriptable,
        values: List[Union[int, float]],
        hold_on: HolderArgs,
        hold_off: HolderArgs,
    ) -> None:
        i: int = 0
        while i < len(values):
            value = values[i]

            await device.execute_command(commands.SetFrequency(int(value))) 
            if hold_on.duration:
                await device.set_signal_on()
            await Holder.execute(hold_on)

            if hold_off.duration:
                await device.set_signal_off()
                await Holder.execute(hold_off)

            i += 1

    async def fetch_args(self, device: Scriptable) -> Dict[str, Any]:
        return {}


class RamperRemote(Ramper):
    def __init__(self) -> None:
        super().__init__()

    @property
    def is_remote(self) -> bool:
        return True

    async def execute(
        self,
        device: Scriptable,
        args: RamperArgs
    ) -> None:
        await device.execute_command(commands.SetRampFStart(args.f_start))
        await device.execute_command(commands.SetRampFStop(args.f_stop))
        await device.execute_command(commands.SetRampFStep(args.f_step))
        # When the args are retrieved from the Form Widget, the HolderArgs are tuples instead
        t_on_duration = int(args.t_on.duration_in_ms)
        t_off_duration = int(args.t_off.duration_in_ms)

        await device.execute_command(commands.SetRampTOn(t_on_duration))
        await device.execute_command(commands.SetRampTOff(t_off_duration))
        await device.execute_command(commands.SetRamp())

    async def fetch_args(self, device: Scriptable) -> Dict[str, Any]:
        answer = await device.execute_command(commands.GetRamp())
        if answer.was_validated and answer.valid:
            return RamperArgs.to_dict_with_holder_args(answer)
        return {}
