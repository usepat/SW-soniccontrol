from typing import Any, Type

import attrs
from attrs import validators

from sonic_protocol.field_names import EFieldName
from sonic_protocol.python_parser import commands
from soniccontrol.procedures.holder import HolderArgs, convert_to_holder_args
from soniccontrol.procedures.procedure import Procedure, ProcedureArgs
from sonic_protocol.command_codes import CommandCode
from soniccontrol.sonic_device import SonicDevice


@attrs.define(auto_attribs=True)
class WipeArgs(ProcedureArgs):
    @classmethod
    def get_description(cls) -> str:
        return """The WIPE procedure is designed for driving our ultrasonic add-ons for cleaning 
(or keeping clean) various inline probes directly in the process.
It is a special protocol optimized to enhance the cleaning effect of ultrasound, whilst not creating hard cavitation to keep probe integrity.
"""     

    f_range: int = attrs.field(
        default=8000,
        metadata={"enum": EFieldName.WIPE_F_RANGE, 'field_view_kwargs': {'SI_unit': 'Hz'}},
        validator=[
            validators.instance_of(int),
            validators.ge(0),
            validators.le(5000000)
        ]
    )
    f_step: int = attrs.field(
        default=1000,
        metadata={"enum": EFieldName.WIPE_F_STEP, 'field_view_kwargs': {'SI_unit': 'Hz'}},
        validator=[
            validators.instance_of(int),
            validators.ge(10),
            validators.le(5000000)
        ]
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
    gain: int = attrs.field(
        default=100,
        validator=[
            validators.instance_of(int),
            validators.ge(0),
            validators.le(150)
        ],
        metadata={"enum": EFieldName.WIPE_GAIN, 'field_view_kwargs': {'SI_unit': '%'}}
    )

class WipeProc(Procedure):    
    @classmethod
    def get_args_class(cls) -> Type: 
        return WipeArgs

    @property
    def is_remote(self) -> bool:
        return True

    async def execute(self, device: SonicDevice, args: WipeArgs, configure_only: bool = False) -> None:
        await device.execute_command(commands.SetWipeFRange(args.f_range))
        await device.execute_command(commands.SetWipeFStep(args.f_step))
        t_on_duration = int(args.t_on.duration_in_ms) if isinstance(args.t_on, HolderArgs) else int(args.t_on[0])
        t_off_duration = int(args.t_off.duration_in_ms) if isinstance(args.t_off, HolderArgs) else int(args.t_off[0])
        t_pause_duration = int(args.t_pause.duration_in_ms) if isinstance(args.t_pause, HolderArgs) else int(args.t_pause[0])

        await device.execute_command(commands.SetWipeTOn(t_on_duration))
        await device.execute_command(commands.SetWipeTOff(t_off_duration))
        await device.execute_command(commands.SetWipeTPause(t_pause_duration))
        if device.has_command(commands.SetWipeGain(args.gain)):
            await device.execute_command(commands.SetWipeGain(args.gain))
        else:
            await device.execute_command(commands.SetGain(args.gain))

        if not configure_only:
            await device.execute_command(commands.SetWipe())

    async def fetch_args(self, device: SonicDevice) -> dict[str, Any]:
        answer = await device.execute_command(commands.GetWipe(), raise_exception=False)
        if answer.was_validated and answer.valid:
            return WipeArgs.to_dict_with_holder_args(answer)
        return {}