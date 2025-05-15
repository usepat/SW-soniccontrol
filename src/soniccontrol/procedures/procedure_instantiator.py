from typing import Dict, Optional
from sonic_protocol.python_parser import commands
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


class ProcedureInstantiator:
    def instantiate_ramp(self, device: SonicDevice) -> Optional[Ramper]:
        if device.has_command(commands.GetSwf()):
            return None # Transducers that have switching frequencies cannot execute the ramp
        elif device.has_command(commands.SetRamp()):
            return RamperRemote()
        else:
            return RamperLocal()
        
    def instantiate_procedures(self, device: SonicDevice) -> Dict[ProcedureType, Procedure]:
        procedures: Dict[ProcedureType, Procedure] = {}

        ramp = self.instantiate_ramp(device)
        if ramp:
            procedures[ProcedureType.RAMP] = ramp

        if device.has_command(commands.SetScan()):
            procedures[ProcedureType.SCAN] = ScanProc()

        if device.has_command(commands.SetAuto()):
            if isinstance(device.communicator, LegacyCommunicator):
                procedures[ProcedureType.AUTO] = AutoLegacyProc()
            else:
                procedures[ProcedureType.AUTO] = AutoProc()

        if device.has_command(commands.SetTune()):
            procedures[ProcedureType.TUNE] = TuneProc()

        if device.has_command(commands.SetWipe()):
            if isinstance(device.communicator, LegacyCommunicator):
                procedures[ProcedureType.WIPE] = WipeLegacyProc()
            else:
                procedures[ProcedureType.WIPE] = WipeProc()

        return procedures
        


