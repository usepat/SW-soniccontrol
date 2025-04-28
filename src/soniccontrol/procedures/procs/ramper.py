from typing import Any, Dict, List, Type, Union
import asyncio

import attrs
from attrs import validators

from sonic_protocol.command_codes import CommandCode
from sonic_protocol.field_names import EFieldName
from soniccontrol.interfaces import Scriptable
from soniccontrol.procedures.holder import Holder, HolderArgs, convert_to_holder_args
from soniccontrol.procedures.procedure import Procedure
from sonic_protocol.python_parser import commands


@attrs.define(auto_attribs=True)
class RamperArgs:
    ramp_f_start: int = attrs.field(validator=[
        validators.instance_of(int),
        validators.ge(0),
        validators.le(10000000)
    ])
    ramp_f_stop: int = attrs.field(validator=[
        validators.instance_of(int),
        validators.ge(0),
        validators.le(10000000)
    ])
    ramp_f_step: int = attrs.field(validator=[
        validators.instance_of(int),
        validators.ge(10),
        validators.le(500000)
    ])
    ramp_t_on: HolderArgs = attrs.field(
        default=HolderArgs(100, "ms"), 
        converter=convert_to_holder_args
    )
    ramp_t_off: HolderArgs = attrs.field(
        default=HolderArgs(0, "ms"),
        converter=convert_to_holder_args
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
        values = [args.ramp_f_start + i * args.ramp_f_step for i in range(int((args.ramp_f_stop - args.ramp_f_start) / args.ramp_f_step)) ]

        await device.get_overview()
        # TODO: Do we need those two lines?
        # await device.execute_command(f"!freq={start}")
        # await device.set_signal_on()
        await self._ramp(device, list(values), args.ramp_t_on, args.ramp_t_off)
    
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

            await device.execute_command(f"!f={value}") # FIXME use internal freq command of device
            if hold_off.duration:
                await device.set_signal_on()
            await Holder.execute(hold_on)

            if hold_off.duration:
                await device.set_signal_off()
                await Holder.execute(hold_off)

            i += 1


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
        await device.execute_command(commands.SetRampArg(CommandCode.SET_RAMP_F_START, args.ramp_f_start))
        await device.execute_command(commands.SetRampArg(CommandCode.SET_RAMP_F_STOP, args.ramp_f_stop))
        await device.execute_command(commands.SetRampArg(CommandCode.SET_RAMP_F_STEP, args.ramp_f_step))
        await device.execute_command(commands.SetRampArg(CommandCode.SET_RAMP_T_ON, int(args.ramp_t_on.duration_in_ms)))
        await device.execute_command(commands.SetRampArg(CommandCode.SET_RAMP_T_OFF, int(args.ramp_t_off.duration_in_ms)))
        await device.execute_command(commands.SetRamp())

    async def fetch_args(self, device: Scriptable) -> Dict[str, Any]:
        answer = await device.execute_command(commands.GetRamp())
        if answer.was_validated and answer.valid:
            return {
                #TODO enforce, that the dictionary fields use the name form the corresponding args
                "ramp_f_start": answer.field_value_dict.get(EFieldName.RAMP_F_START, 0),
                "ramp_f_stop": answer.field_value_dict.get(EFieldName.RAMP_F_STOP, 0),
                "ramp_f_step": answer.field_value_dict.get(EFieldName.RAMP_F_STEP, 0),
                "ramp_t_on": HolderArgs(float(answer.field_value_dict.get(EFieldName.RAMP_T_ON, 0)), "ms"),
                "ramp_t_off": HolderArgs(float(answer.field_value_dict.get(EFieldName.RAMP_T_OFF, 0)), "ms"),
            }
        return {}
