
from typing import Any, List, Type, Union
import asyncio
import attrs

from sonic_protocol.python_parser import commands
from sonic_protocol.schema import SIPrefix
from soniccontrol.sonic_device import SonicDevice
from soniccontrol.updater import Updater
from soniccontrol.procedures.holder import Holder, HolderArgs, convert_to_holder_args
from soniccontrol.procedures.procedure import Procedure, custom_validator_factory
from sonic_protocol.si_unit import cls_converter, AbsoluteFrequencySIVar, GainSIVar, RelativeFrequencySIVar


@attrs.define(auto_attribs=True)
class SpectrumMeasureArgs:
    @classmethod
    def get_description(cls) -> str:
        return """Spectrum Measure measures the electric response of the connected add-on over the frequency.
This is very useful in an explorative study to find the optimal driving frequency.
"""
    
    gain: GainSIVar = attrs.field(
        default=GainSIVar(20),
        converter=cls_converter(GainSIVar),
    )

    f_start: AbsoluteFrequencySIVar = attrs.field(
        default=AbsoluteFrequencySIVar(1000000),
        converter=cls_converter(AbsoluteFrequencySIVar),
    )
    
    f_stop: AbsoluteFrequencySIVar = attrs.field(
        default=AbsoluteFrequencySIVar(2000000),
        converter=cls_converter(AbsoluteFrequencySIVar)
    )
    
    f_step: RelativeFrequencySIVar = attrs.field(
        default=RelativeFrequencySIVar(100000),
        converter=cls_converter(RelativeFrequencySIVar),
        validator=custom_validator_factory(RelativeFrequencySIVar, RelativeFrequencySIVar(10), RelativeFrequencySIVar(5, SIPrefix.MEGA))
    )

    t_on: HolderArgs = attrs.field(
        default=HolderArgs(1000, "ms"),
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
        self._stop_requested = asyncio.Event()

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
        self._stop_requested.clear()
        f_start = int(args.f_start.to_prefix(SIPrefix.NONE))
        f_stop = int(args.f_stop.to_prefix(SIPrefix.NONE))
        f_step = int(args.f_step.to_prefix(SIPrefix.NONE))

        num_steps = (f_stop - f_start) // f_step
        values = [f_start + i * f_step for i in range(num_steps + 1) ] # +1, because range stop is exclusive

        try:
            self._raise_if_stop_requested()
            await device.execute_command(commands.SetGain(args.gain.to_prefix(SIPrefix.NONE)))
            await self._ramp(device, list(values), args.t_on, args.t_off, args.time_offset_measure)
        finally:
            await device.set_signal_off()

    def request_stop(self) -> bool:
        self._stop_requested.set()
        return True

    def _raise_if_stop_requested(self) -> None:
        if self._stop_requested.is_set():
            raise asyncio.CancelledError()

    async def _wait_or_stop(self, args: HolderArgs) -> None:
        self._raise_if_stop_requested()
        hold_task = asyncio.create_task(Holder.execute(args))
        stop_task = asyncio.create_task(self._stop_requested.wait())

        done, pending = await asyncio.wait(
            {hold_task, stop_task},
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()

        if stop_task in done:
            hold_task.cancel()
            raise asyncio.CancelledError()

        await hold_task

    async def _ramp(
        self,
        device: SonicDevice,
        values: List[Union[int, float]],
        hold_on: HolderArgs,
        hold_off: HolderArgs,
        time_offset_measure: HolderArgs
    ) -> None:
        for i, value in enumerate(values):
            self._raise_if_stop_requested()
            await device.execute_command(commands.SetFrequency(int(value)))
            if hold_off.duration or i == 0:
                await device.set_signal_on()

            await self._wait_or_stop(time_offset_measure)
            self._raise_if_stop_requested()
            await self._updater.update()
            await self._wait_or_stop(hold_on - time_offset_measure)

            if hold_off.duration:
                await device.set_signal_off()
                await self._wait_or_stop(hold_off)

    async def fetch_args(self, device: SonicDevice) -> dict[str, Any]:
        return {}



if __name__ == "__main__":
    spectrum_args=SpectrumMeasureArgs(
           gain=10,
           f_start=int(2.0e6),
           f_stop=int(2.2e6),
           f_step=int(500),
           t_on=(350, 'ms'),
           time_offset_measure=(200, 'ms'),
    )
    print(spectrum_args)