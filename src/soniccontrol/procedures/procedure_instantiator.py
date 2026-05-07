from typing import Dict, Optional
from sonic_protocol.python_parser import commands
from sonic_protocol.python_parser.commands import Command
from soniccontrol.procedures.procedure import Procedure, ProcedureType
from soniccontrol.procedures.procs.auto import AutoProc
from soniccontrol.procedures.procs.ramper import Ramper, RamperLocal, RamperRemote
from soniccontrol.procedures.procs.scan import ScanProc
from soniccontrol.procedures.procs.tune import TuneProc
from soniccontrol.procedures.procs.wipe import WipeProc
from soniccontrol.procedures.legacy_procs.auto import AutoLegacyProc
from soniccontrol.procedures.legacy_procs.wipe import WipeLegacyProc
from soniccontrol.sonic_device import SonicDevice
from soniccontrol.communication.legacy_communicator import LegacyCommunicator
from typing import Tuple, List


class ProcedureInstantiator:
    async def _is_command_valid(self, device: SonicDevice, cmd: Command) -> bool:
        if device.has_command(cmd):
            answer = await device.execute_command(cmd, raise_exception=False)
            return answer.valid
        return False
        
        
    async def instantiate_procedures(self, device: SonicDevice) -> Dict[ProcedureType, Procedure]:
        procedures: Dict[ProcedureType, Procedure] = {}

        proc_inst_descriptors: List[Tuple[ProcedureType, Command, Procedure]] = [
            (ProcedureType.RAMP, commands.GetRamp(), RamperRemote()),
            (ProcedureType.SCAN, commands.GetScan(), ScanProc()),
            (ProcedureType.AUTO, commands.GetAuto(), AutoProc()),
            (ProcedureType.TUNE, commands.GetTune(), TuneProc()),
            (ProcedureType.WIPE, commands.GetWipe(), WipeProc())
        ]

        for proc_type, cmd, proc in proc_inst_descriptors:
            if await self._is_command_valid(device, cmd):
                # if procedures are not enabled the get and set proc commands are returning an error
                procedures[proc_type] = proc

        if device.has_command(commands.SetWipeLegacy()):
            procedures[ProcedureType.WIPE_LEGACY] = WipeLegacyProc()

        if device.has_command(commands.SetAutoLegacy()):
            procedures[ProcedureType.AUTO_LEGACY] = AutoLegacyProc()

        if ProcedureType.RAMP not in procedures and device.has_command(commands.GetFreq()):
            # for old devices that are no descale (ergo have no swf and use normal freq)
            # we provide a sonic control implementation of ramp, so that the scripts are usable with that
            procedures[ProcedureType.RAMP] = RamperLocal()

        return procedures
        


