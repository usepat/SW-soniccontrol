import asyncio
from typing import Any, Type

import attrs
from attrs import validators

from sonic_protocol.command_codes import CommandCode
from sonic_protocol.field_names import EFieldName
from sonic_protocol.python_parser import commands
from soniccontrol.interfaces import Scriptable
from soniccontrol.procedures.holder import HolderArgs, convert_to_holder_args
from soniccontrol.procedures.procedure import Procedure, ProcedureArgs


@attrs.define(auto_attribs=True, init=False)
class TuneArgs(ProcedureArgs):
    @classmethod
    def get_description(cls) -> str:
        return """The TUNE procedure is designed to tune the driving frequency to create the optimal field for the intended application.
        It is helpful when certain parameters are expected to change significantly, e.g. temperature, liquid composition etc.
        """
    
    f_step: int = attrs.field(
        default=1000,
        validator=[
            validators.instance_of(int),
            validators.ge(0),
            validators.le(5000000)
        ],
        metadata={"enum": EFieldName.TUNE_F_STEP}
    )
    t_time: HolderArgs = attrs.field(
        default=HolderArgs(100, "ms"), 
        converter=convert_to_holder_args,
        metadata={"enum": EFieldName.TUNE_T_TIME}
    )

    n_steps: int = attrs.field(
        default=3,
        validator=[
            validators.instance_of(int),
            validators.ge(0),
            validators.le(20)
        ],
        metadata={"enum": EFieldName.TUNE_N_STEPS}
    )

    f_shift: int = attrs.field(
        default=0,
        validator=[
            validators.instance_of(int),
            validators.ge(0),
            validators.le(5000000)
        ],
        metadata={"enum": EFieldName.TUNE_F_SHIFT}
    )

    t_step: HolderArgs = attrs.field(
        default=HolderArgs(100, "ms"), 
        converter=convert_to_holder_args,
        metadata={"enum": EFieldName.TUNE_T_STEP}
    )

    # TODO Enable for the next procotol version
    # gain: int = attrs.field(
    #     default=80,
    #     validator=[
    #         validators.instance_of(int),
    #         validators.ge(0),
    #         validators.le(150)
    #     ],
    #     metadata={"enum": EFieldName.TUNE_GAIN}
    # )

class TuneProc(Procedure):
    @classmethod
    def get_args_class(cls) -> Type: 
        return TuneArgs

    @property
    def is_remote(self) -> bool:
        return True

    async def execute(self, device: Scriptable, args: TuneArgs, start: bool = True) -> None:
        # TODO enable in next procotol
        # await device.execute_command(commands.SetTuneGain(args.gain))
        await device.execute_command(commands.SetTuneFShift(args.f_shift))
        await device.execute_command(commands.SetTuneNSteps(args.n_steps))
        await device.execute_command(commands.SetTuneFStep(args.f_step))
        t_time_duration = int(args.t_time.duration_in_ms) if isinstance(args.t_time, HolderArgs) else int(args.t_time[0])
        t_step_duration = int(args.t_step.duration_in_ms) if isinstance(args.t_step, HolderArgs) else int(args.t_step[0])

        await device.execute_command(commands.SetTuneTTime(t_time_duration))
        await device.execute_command(commands.SetTuneTStep(t_step_duration))
        if start:
            await device.execute_command(commands.SetTune())


    async def fetch_args(self, device: Scriptable) -> dict[str, Any]:
        answer = await device.execute_command(commands.GetTune())
        if answer.was_validated and answer.valid:
            return TuneArgs.to_dict_with_holder_args(answer)
        return {}
