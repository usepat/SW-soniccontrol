
import asyncio
from typing import Any, List, Type, Union
import attrs
from attrs import validators

from sonic_protocol.python_parser import commands
from sonic_protocol.schema import SIPrefix
from soniccontrol.sonic_device import SonicDevice
from soniccontrol.updater import Updater
from soniccontrol.procedures.holder import Holder, HolderArgs, convert_to_holder_args
from soniccontrol.procedures.procedure import Procedure, custom_validator_factory
from sonic_protocol.si_unit import AbsoluteFrequencySIVar, GainSIVar, RelativeFrequencySIVar


@attrs.define(auto_attribs=True)
class SpectrumMeasureArgs:
    @classmethod
    def get_description(cls) -> str:
        return """Spectrum Measure measures the electric response of the connected add-on over the frequency.
This is very useful in an explorative study to find the optimal driving frequency.
"""
    
    gain: GainSIVar = attrs.field()

    f_start: AbsoluteFrequencySIVar = attrs.field()
    
    f_stop: AbsoluteFrequencySIVar = attrs.field()
    
    f_step: RelativeFrequencySIVar = attrs.field(
        validator=custom_validator_factory(RelativeFrequencySIVar, RelativeFrequencySIVar(10), RelativeFrequencySIVar(5, SIPrefix.MEGA))
    )

    t_on: HolderArgs = attrs.field(
        default=HolderArgs(100, "ms"),
        converter=convert_to_holder_args,
    )
    t_off: HolderArgs = attrs.field(
        default=HolderArgs(0, "ms"),
        converter=convert_to_holder_args,
    )

    time_offset_measure: HolderArgs = attrs.field(
        default=HolderArgs(100, "ms"), 
        converter=convert_to_holder_args,
    )


class SpectrumMeasure(Procedure):
    def __init__(self, updater: Updater) -> None:
        self._updater = updater        

    @classmethod
    def get_args_class(cls) -> Type: 
        return SpectrumMeasureArgs

    @property
    def is_remote(self) -> bool:
        return False

    async def execute(
        self,
        device: SonicDevice,
        args: SpectrumMeasureArgs
    ) -> None:
        values = [args.f_start.to_prefix(SIPrefix.NONE) + i * args.f_step.to_prefix(SIPrefix.NONE) for i in range(int((args.f_stop.to_prefix(SIPrefix.NONE) - args.f_start.to_prefix(SIPrefix.NONE)) / args.f_step.to_prefix(SIPrefix.NONE))) ]

        try:
            # await device.get_overview() # FIXME I dont think we need this
            # I am removing it for now because we can't send commands to the crystal device that have no command code
            await device.execute_command(commands.SetGain(args.gain.to_prefix(SIPrefix.NONE)))
            await self._ramp(device, list(values), args.t_on, args.t_off, args.time_offset_measure)
        finally:
            await device.set_signal_off()

    async def _ramp(
        self,
        device: SonicDevice,
        values: List[Union[int, float]],
        hold_on: HolderArgs,
        hold_off: HolderArgs,
        time_offset_measure: HolderArgs
    ) -> None:
        for i, value in enumerate(values):
            await device.execute_command(commands.SetFrequency(int(value)))
            if hold_off.duration or i == 0:
                await device.set_signal_on()

            await Holder.execute(time_offset_measure)
            asyncio.get_running_loop().create_task(self._updater.update())
            await Holder.execute(hold_on - time_offset_measure)

            if hold_off.duration:
                await device.set_signal_off()
                await Holder.execute(hold_off)

    async def fetch_args(self, device: SonicDevice) -> dict[str, Any]:
        return {}


