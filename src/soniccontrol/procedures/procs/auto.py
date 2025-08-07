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

    async def execute(self, device: SonicDevice, args: AutoArgs, configure_only: bool = False) -> None:
        scan = ScanProc()
        # With False we only execute the arg setter
        await scan.execute(device, args.scan_arg, False)

        tune = TuneProc()
        await tune.execute(device, args.tune_arg, False)
        
        if not configure_only:
            await device.execute_command(commands.SetAuto())

    async def fetch_args(self, device: SonicDevice) -> dict[str, Any]:
        try:
            # TODO ensure GetAuto returns a answer where all FieldName of both scan and tune are returned
            answer = await device.execute_command(commands.GetAuto())
        except (CommandValidationError, CommandExecutionError) as _:
            return {}
    
        # This is just a workaround at the moment
        # TODO: refactor the procedure convert functions for dicts and tuples.
        scan_args = ScanArgs.to_dict_with_holder_args(answer)
        tune_args = TuneArgs.to_dict_with_holder_args(answer)

        return {"scan_arg": scan_args, "tune_arg": tune_args}
