
import asyncio
from typing import Any, Dict, List, Type, Union
from attrs import validators
import attrs

from sonic_protocol.python_parser import commands
from soniccontrol_gui.state_fetching.updater import Updater
from soniccontrol.interfaces import Scriptable
from soniccontrol.procedures.holder import Holder, HolderArgs, convert_to_holder_args
from soniccontrol.procedures.procedure import Procedure
from soniccontrol.procedures.procs.ramper import RamperArgs

@attrs.define()
class SpectrumMeasureModel:
    form_fields: Dict[str, Any] = attrs.field(default={})

@attrs.define()
class SpectrumMeasureArgs(RamperArgs):
    time_offset_measure: HolderArgs = attrs.field(
        default=HolderArgs(100, "ms"), 
        converter=convert_to_holder_args
    )


class SpectrumMeasure(Procedure):
    def __init__(self, updater: Updater) -> None:
        self._updater = updater        

    @classmethod
    def get_args_class(cls) -> Type: 
        return SpectrumMeasureArgs

    async def execute(
        self,
        device: Scriptable,
        args: SpectrumMeasureArgs
    ) -> None:
        start = args.freq_center - args.half_range
        stop = args.freq_center + args.half_range + args.step # add a step to stop so that stop is inclusive
        values = [start + i * args.step for i in range(int((stop - start) / args.step)) ]

        try:
            await self._updater.stop()
            await device.get_overview()
            await self._ramp(device, list(values), args.hold_on, args.hold_off)
        finally:
            await device.set_signal_off()
            self._updater.start()

    async def _ramp(
        self,
        device: Scriptable,
        values: List[Union[int, float]],
        hold_on: HolderArgs,
        hold_off: HolderArgs,
    ) -> None:
        for  i in range(len(values)):
            value = int(values[i])

            await device.execute_command(commands.SetFrequency(value))
            if hold_off.duration:
                await device.set_signal_on()
            asyncio.get_running_loop().create_task(self._updater.update())
            await Holder.execute(hold_on)

            if hold_off.duration:
                await device.set_signal_off()
                await Holder.execute(hold_off)


