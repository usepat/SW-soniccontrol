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
class WipeLegacyArgs(ProcedureArgs):
    @classmethod
    def get_description(cls) -> str:
        return """The WIPE procedure is designed for driving our ultrasonic add-ons for cleaning 
(or keeping clean) various inline probes directly in the process.
It is a special protocol optimized to enhance the cleaning effect of ultrasound, whilst not creating hard cavitation to keep probe integrity.
"""   

    # TODO set correct limits and defaults
    step: int = attrs.field(
        default=500,
        metadata={"enum": EFieldName.LEGACY_STEP},
        validator=[
            validators.instance_of(int),
            validators.ge(0),
            validators.le(5000000)
        ]
    )
    sing: HolderArgs = attrs.field(
        default=HolderArgs(500, "ms"),
        metadata={"enum": EFieldName.LEGACY_SING},
        converter=convert_to_holder_args
    )
    paus: HolderArgs = attrs.field(
        default=HolderArgs(500, "ms"), 
        metadata={"enum": EFieldName.LEGACY_PAUS},
        converter=convert_to_holder_args
    )
    rang: int = attrs.field(
        default=8000, 
        metadata={"enum": EFieldName.LEGACY_RANG},
        validator=[
            validators.instance_of(int),
            validators.ge(0),
            validators.le(5000000)
        ]
    )

class WipeLegacyProc(Procedure):    
    @classmethod
    def get_args_class(cls) -> Type: 
        return WipeLegacyArgs

    @property
    def is_remote(self) -> bool:
        return True

    async def execute(self, device: Scriptable, args: WipeLegacyArgs) -> None:
        await device.execute_command(commands.SetStepLegacy(args.step))
        await device.execute_command(commands.SetRangLegacy(args.rang))
        sing_duration = int(args.sing.duration_in_ms) if isinstance(args.sing, HolderArgs) else int(args.sing[0])
        paus_duration = int(args.paus.duration_in_ms) if isinstance(args.paus, HolderArgs) else int(args.paus[0])
        await device.execute_command(commands.SetSingLegacy(sing_duration))
        await device.execute_command(commands.SetPausLegacy(paus_duration))

        await device.execute_command(commands.SetWipeLegacy())

    async def fetch_args(self, device: Scriptable) -> dict[str, Any]:
        answer = await device.execute_command(commands.GetPvalLegacy())
        if answer.was_validated and answer.valid:
            return WipeLegacyArgs.to_dict_with_holder_args(answer)
        return {}