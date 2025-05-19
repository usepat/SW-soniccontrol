import logging
from typing import Any, Dict, Literal, Optional, Type
import asyncio

from sonic_protocol.field_names import EFieldName
import sonic_protocol.defs as protocol_defs
import sonic_protocol.python_parser.commands as cmds
from soniccontrol.procedures.procedure import Procedure, ProcedureType
from soniccontrol.procedures.procedure_instantiator import ProcedureInstantiator
from soniccontrol.procedures.remote_procedure_state import RemoteProcedureState
from soniccontrol.sonic_device import SonicDevice
from soniccontrol.logging_utils import get_base_logger
from soniccontrol.events import Event, EventManager

class ProcedureController(EventManager):
    PROCEDURE_STOPPED: Literal["<<PROCEDURE_STOPPED>>"] = "<<PROCEDURE_STOPPED>>"
    PROCEDURE_RUNNING: Literal["<<PROCEDURE_RUNNING>>"] = "<<PROCEDURE_RUNNING>>"

    def __init__(self, device: SonicDevice, updater: EventManager, logger = None): # TODO: add type hint to updater after moving updater into sonic control
        super().__init__()
        if logger is None:
            logger = get_base_logger(device._logger)
        self._logger = logging.getLogger(logger.name + "." + ProcedureController.__name__)
        self._device = device

        self._logger.debug("Instantiate procedures")
        proc_instantiator = ProcedureInstantiator()
        self._procedures: Dict[ProcedureType, Procedure] = proc_instantiator.instantiate_procedures(self._device)
        self._ramp: Optional[Procedure] = self._procedures.get(ProcedureType.RAMP, None)
        self._running_proc_task: Optional[asyncio.Task] = None
        self._remote_procedure_state = RemoteProcedureState()

        updater.subscribe("update", self._on_update)

    @property
    def proc_args_list(self) -> Dict[ProcedureType, Type]:
        return { 
            proc_type: procedure.get_args_class() 
            for proc_type, procedure in self._procedures.items() 
        }

    @property
    def is_proc_running(self) -> bool:
        return not (self._running_proc_task is None or self._running_proc_task.done() or self._running_proc_task.cancelled())

    def execute_proc(self, proc_type: ProcedureType, args: Any, event_loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()) -> None:
        assert(proc_type in self._procedures)
        procedure = self._procedures.get(proc_type, None)
        if procedure is None:
            raise Exception(f"The procedure {repr(proc_type)} is not available for the current device")
       
        self.execute_procedure(procedure, proc_type, args, event_loop)

    def execute_procedure(self, procedure: Procedure, proc_type: ProcedureType, args: Any, event_loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()):
        if self.is_proc_running:
            raise Exception("There is already a procedure running")
        
        self._logger.info("Run procedure %s with args %s", proc_type.name, str(args))
    

        async def proc_task():
            try:
                await procedure.execute(self._device, args)
                if procedure.is_remote:
                    await self._remote_procedure_state.wait_till_procedure_halted()          
            except Exception as e:
                if procedure.is_remote:
                    if self._device.has_command(cmds.SetStop()):
                        await self._device.execute_command(cmds.SetStop())
                    else:
                        await self._device.execute_command(cmds.SetOff())
                await self._device.set_signal_off()
                if not isinstance(e, asyncio.CancelledError):
                    raise e # if task was not cancelled, then some internal unexpected exception occurred
            finally:
                self._on_proc_finished()

        self._remote_procedure_state.reset_completion_flag()
        self._running_proc_task = event_loop.create_task(proc_task())
        self.emit(Event(ProcedureController.PROCEDURE_RUNNING, proc_type=proc_type))

    async def fetch_args(self, proc_type: ProcedureType) -> Dict[str, Any]:
        assert(proc_type in self._procedures)
        procedure = self._procedures.get(proc_type, None)
        if procedure is None:
            raise Exception(f"The procedure {repr(proc_type)} is not available for the current device")
        return await procedure.fetch_args(self._device)


    async def stop_proc(self) -> None:
        self._logger.info("Stop procedure")
        if self._device.has_command(cmds.SetStop()):
            await self._device.execute_command(cmds.SetStop())
        else:
            await self._device.execute_command(cmds.SetOff())
        if self._running_proc_task: 
            self._running_proc_task.cancel()
            await self._running_proc_task

    async def wait_for_proc_to_finish(self) -> None:
        await self._remote_procedure_state.wait_till_procedure_halted()

    def _on_proc_finished(self) -> None:
        self._logger.info("Procedure stopped")
        self._running_proc_task = None
        self.emit(Event(ProcedureController.PROCEDURE_STOPPED))

    def _on_update(self, event: Event) -> None:
        try:
            procedure: protocol_defs.Procedure = event.data["status"][EFieldName.PROCEDURE]
        except KeyError:
            self._logger.debug("No procedure status found in event")
            return
        proc_type: ProcedureType | None = None
        match procedure:
            case protocol_defs.Procedure.NO_PROC:
                proc_type = None
            case protocol_defs.Procedure.AUTO:
                proc_type = ProcedureType.AUTO
            case protocol_defs.Procedure.WIPE:
                proc_type = ProcedureType.WIPE
            case protocol_defs.Procedure.TUNE:
                proc_type = ProcedureType.TUNE
            case protocol_defs.Procedure.SCAN:
                proc_type = ProcedureType.SCAN
            case protocol_defs.Procedure.RAMP:
                proc_type = ProcedureType.RAMP
            case _:
                assert False, "Case not covered"
        self._remote_procedure_state.update(proc_type)
