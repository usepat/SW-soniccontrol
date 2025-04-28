
import asyncio
from typing import Any, List, Type, Union
import attrs

from sonic_protocol.python_parser import commands
from soniccontrol.updater import Updater
from soniccontrol.interfaces import Scriptable
from soniccontrol.procedures.holder import Holder, HolderArgs, convert_to_holder_args
from soniccontrol.procedures.procedure import Procedure
from soniccontrol.procedures.procs.ramper import RamperArgs

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

    @property
    def is_remote(self) -> bool:
        return False

    async def execute(
        self,
        device: Scriptable,
        args: SpectrumMeasureArgs
    ) -> None:
        values = [args.ramp_f_start + i * args.ramp_f_step for i in range(int((args.ramp_f_stop - args.ramp_f_start) / args.ramp_f_step)) ]

        try:
            await device.get_overview()
            await self._ramp(device, list(values), args.ramp_t_on, args.ramp_t_off, args.time_offset_measure)
        finally:
            await device.set_signal_off()

    async def _ramp(
        self,
        device: Scriptable,
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

    async def fetch_args(self, device: Scriptable) -> dict[str, Any]:
        return {}


