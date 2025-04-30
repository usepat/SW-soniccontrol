import asyncio
from typing import Any, Type

import attrs
from attrs import validators

from sonic_protocol.command_codes import CommandCode
from sonic_protocol.field_names import EFieldName
from sonic_protocol.python_parser import commands
from soniccontrol.interfaces import Scriptable
from soniccontrol.procedures.procedure import Procedure, ProcedureArgs
from soniccontrol.procedures.procs.scan import ScanArgs, ScanProc
from soniccontrol.procedures.procs.tune import TuneArgs, TuneProc


@attrs.define(auto_attribs=True, init=False)
class AutoArgs(ProcedureArgs):
    scan_arg: ScanArgs = attrs.field(
        default=ScanArgs(),
    )
    tune_arg: TuneArgs = attrs.field(
        default=TuneArgs(),
    )


class AutoProc(Procedure):
    @classmethod
    def get_args_class(cls) -> Type: 
        return AutoArgs
    
    @property
    def is_remote(self) -> bool:
        return True

    async def execute(self, device: Scriptable, args: AutoArgs) -> None:
        scan = ScanProc()
        # With False we only execute the arg setter
        await scan.execute(device, args.scan_arg, False)

        tune = TuneProc()
        await tune.execute(device, args.tune_arg, False)
        await device.execute_command(commands.SetAuto())

    async def fetch_args(self, device: Scriptable) -> dict[str, Any]:
        # TODO ensure GetAuto returns a answer where all FieldName of both scan and tune are returned
        answer = await device.execute_command(commands.GetAuto())
        if answer.was_validated and answer.valid:
            return AutoArgs.to_dict_with_holder_args(answer)
        return {}