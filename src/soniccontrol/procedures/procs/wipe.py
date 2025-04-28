from typing import Any, Type

import attrs
from attrs import validators

from sonic_protocol.field_names import EFieldName
from sonic_protocol.python_parser import commands
from soniccontrol.interfaces import Scriptable
from soniccontrol.procedures.holder import HolderArgs, convert_to_holder_args
from soniccontrol.procedures.procedure import Procedure
from sonic_protocol.command_codes import CommandCode


@attrs.define(auto_attribs=True)
class WipeArgs:
    wipe_f_range: int = attrs.field(validator=[
        validators.instance_of(int),
        validators.ge(0),
        validators.le(5000000)
    ])
    wipe_f_step: int = attrs.field(validator=[
        validators.instance_of(int),
        validators.ge(10),
        validators.le(5000000)
    ])
    wipe_t_on: HolderArgs = attrs.field(
        default=HolderArgs(100, "ms"), 
        converter=convert_to_holder_args
    )
    wipe_t_off: HolderArgs = attrs.field(
        default=HolderArgs(0, "ms"), 
        converter=convert_to_holder_args
    )
    wipe_t_pause: HolderArgs = attrs.field(
        default=HolderArgs(1000, "ms"), 
        converter=convert_to_holder_args
    )

class WipeProc(Procedure):
    @classmethod
    def get_args_class(cls) -> Type: 
        return WipeArgs

    @property
    def is_remote(self) -> bool:
        return True

    async def execute(self, device: Scriptable, args: WipeArgs) -> None:
        await device.execute_command(commands.SetWipeArg(CommandCode.SET_WIPE_F_RANGE, args.wipe_f_range))
        await device.execute_command(commands.SetWipeArg(CommandCode.SET_WIPE_F_STEP, args.wipe_f_step))
        await device.execute_command(commands.SetWipeArg(CommandCode.SET_WIPE_T_ON, int(args.wipe_t_on.duration_in_ms)))
        await device.execute_command(commands.SetWipeArg(CommandCode.SET_WIPE_T_OFF, int(args.wipe_t_off.duration_in_ms)))
        await device.execute_command(commands.SetWipeArg(CommandCode.SET_WIPE_T_PAUSE, int(args.wipe_t_pause.duration_in_ms)))
        await device.execute_command(commands.SetWipe())

    async def fetch_args(self, device: Scriptable) -> dict[str, Any]:
        answer = await device.execute_command(commands.GetWipe())
        if answer.was_validated and answer.valid:
            return {
                "wipe_f_range": answer.field_value_dict.get(EFieldName.WIPE_F_RANGE, 0),
                "wipe_f_step": answer.field_value_dict.get(EFieldName.WIPE_F_STEP, 0),
                "wipe_t_on": HolderArgs(float(answer.field_value_dict.get(EFieldName.WIPE_T_ON, 0)), "ms"),
                "wipe_t_off": HolderArgs(float(answer.field_value_dict.get(EFieldName.WIPE_T_OFF, 0)), "ms"),
                "wipe_t_pause":  HolderArgs(float(answer.field_value_dict.get(EFieldName.WIPE_T_PAUSE, 0)), "ms"),
            }
        return {}