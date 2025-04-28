from typing import Any, Dict, List, Type, Union
import asyncio

import attrs
from attrs import fields, validators

from sonic_protocol.command_codes import CommandCode
from sonic_protocol.field_names import EFieldName
from soniccontrol.interfaces import Scriptable
from soniccontrol.procedures.holder import Holder, HolderArgs, convert_to_holder_args
from soniccontrol.procedures.procedure import Procedure, ProcedureArgs
from sonic_protocol.python_parser import commands


@attrs.define(auto_attribs=True)
class RamperArgs(ProcedureArgs):
    f_start: int = attrs.field(
        validator=[
            validators.instance_of(int),
            validators.ge(0),
            validators.le(10_000_000)
        ],
        metadata={"enum": EFieldName.RAMP_F_START}
    )
    f_stop: int = attrs.field(
        validator=[
            validators.instance_of(int),
            validators.ge(0),
            validators.le(10_000_000)
        ],
        metadata={"enum": EFieldName.RAMP_F_STOP}
    )
    f_step: int = attrs.field(
        validator=[
            validators.instance_of(int),
            validators.ge(10),
            validators.le(500_000)
        ],
        metadata={"enum": EFieldName.RAMP_F_STEP}
    )
    t_on: HolderArgs = attrs.field(
        default=HolderArgs(100, "ms"),
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
        values = [args.f_start + i * args.f_step for i in range(int((args.f_stop - args.f_start) / args.f_step)) ]

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
        await device.execute_command(commands.SetRampFStart(args.f_start))
        await device.execute_command(commands.SetRampFStop(args.f_stop))
        await device.execute_command(commands.SetRampFStep(args.f_step))
        await device.execute_command(commands.SetRampTOn(int(args.t_on.duration_in_ms)))
        await device.execute_command(commands.SetRampTOff(int(args.t_off.duration_in_ms)))
        await device.execute_command(commands.SetRamp())

    async def fetch_args(self, device: Scriptable) -> Dict[str, Any]:
        answer = await device.execute_command(commands.GetRamp())

        if not (answer.was_validated and answer.valid):
            return {}

        # Work directly on answer.field_value_dict
        arg_dict = {}
        for field in fields(RamperArgs):
            enum = field.metadata.get("enum", field.name)

            if enum in answer.field_value_dict:
                value = answer.field_value_dict.get(enum)

                # If it's a _t_ field, wrap in HolderArgs
                if value is None:
                    continue
                if "_t_" in enum.value:
                    value = HolderArgs(float(value), "ms")

                # Set the new key with the alias
                arg_dict[enum.value] = value

        return arg_dict
