from typing import Any, Type

import attrs

from sonic_protocol.python_parser import commands
from soniccontrol.procedures.procedure import Procedure, ProcedureArgs
from soniccontrol.procedures.procs.scan import ScanArgs, ScanProc
from soniccontrol.procedures.procs.tune import TuneArgs, TuneProc
from soniccontrol.sonic_device import CommandExecutionError, CommandValidationError, SonicDevice


@attrs.define(auto_attribs=True)
class AutoArgs(ProcedureArgs):    
    @classmethod
    def get_description(cls) -> str:
        return """The AUTO procedure starts by executing the SCAN procedure, and when finished, immediately starts the TUNE procedure.
        """

    scan_arg: ScanArgs = attrs.field(
        default=ScanArgs(),
        metadata={"prefix": "scan"},
    )
    tune_arg: TuneArgs = attrs.field(
        default=TuneArgs(),
        metadata={"prefix": "tune"},
    )


class AutoProc(Procedure):
    @classmethod
    def get_args_class(cls) -> Type: 
        return AutoArgs
    
    @property
    def is_remote(self) -> bool:
        return True

    async def execute(self, device: SonicDevice, args: AutoArgs, configure_only: bool = False) -> None:
        scan = ScanProc()
        # With True we only execute the arg setter
        await scan.execute(device, args.scan_arg, True)

        tune = TuneProc()
        await tune.execute(device, args.tune_arg, True)
        
        if not configure_only:
            await device.execute_command(commands.SetAuto())

    async def fetch_args(self, device: SonicDevice) -> dict[str, Any]:
        try:
            # TODO ensure GetAuto returns a answer where all FieldName of both scan and tune are returned
            answer = await device.execute_command(commands.GetAuto())
        except (CommandValidationError, CommandExecutionError) as _:
            return {}
        args = AutoArgs.from_answer(answer)
        # Returns nested dicts for the form widget
        return args.to_dict()
