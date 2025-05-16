from typing import Any, Type

import attrs
from attrs import validators

from sonic_protocol.field_names import EFieldName
from sonic_protocol.python_parser import commands
from soniccontrol.interfaces import Scriptable
from soniccontrol.procedures.holder import HolderArgs, convert_to_holder_args
from soniccontrol.procedures.procedure import Procedure, ProcedureArgs
from sonic_protocol.command_codes import CommandCode


@attrs.define(auto_attribs=True, init=False)
class AutoLegacyArgs(ProcedureArgs):
    @classmethod
    def get_description(cls) -> str:
        return "No description"

    # TODO set correct limits and defaults
    tust: int = attrs.field(
        default=8000,
        metadata={"enum": EFieldName.LEGACY_TUST},
        validator=[
            validators.instance_of(int),
            validators.ge(0),
            validators.le(5000000)
        ]
    )
    tutm: HolderArgs = attrs.field(
        default=HolderArgs(500, "ms"),
        metadata={"enum": EFieldName.LEGACY_TUTM},
        converter=convert_to_holder_args
    )
    scst: int = attrs.field(
        default=1000, 
        metadata={"enum": EFieldName.LEGACY_SCST},
        validator=[
            validators.instance_of(int),
            validators.ge(0),
            validators.le(5000000)
        ]
    )

class AutoLegacyProc(Procedure):    
    @classmethod
    def get_args_class(cls) -> Type: 
        return AutoLegacyArgs

    @property
    def is_remote(self) -> bool:
        return True

    async def execute(self, device: Scriptable, args: AutoLegacyArgs) -> None:
        #await device.execute_command(commands.SetTustLegacy(args.tust))
        #await device.execute_command(commands.SetScstLegacy(args.scst))
        tutm_duration = int(args.tutm.duration_in_ms) if isinstance(args.tutm, HolderArgs) else int(args.tutm[0])
        #await device.execute_command(commands.SetTutmLegacy(tutm_duration))

        await device.execute_command(commands.SetAutoLegacy())

    async def fetch_args(self, device: Scriptable) -> dict[str, Any]:
        # answer = await device.execute_command(commands.GetPvalLegacy())
        # if answer.was_validated and answer.valid:
        #     return AutoLegacyArgs.to_dict_with_holder_args(answer)
        return {}