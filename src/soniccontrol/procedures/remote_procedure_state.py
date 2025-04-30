import asyncio
from soniccontrol.events import Event, EventManager
from soniccontrol.procedures.procedure import ProcedureType


class RemoteProcedureState(EventManager):
    PROCEDURE_HALTED = "<<PROCEDURE_HALTED>>"

    def __init__(self):
        super().__init__()
        self._current_proc: ProcedureType | None = None
        self._halted: asyncio.Event = asyncio.Event()

    def update(self, proc_type: ProcedureType | None):
        if proc_type != self._current_proc:
            if proc_type is None:
                # When no proc is running, than the procedure halted
                self._halted.set()
                self.emit(Event(RemoteProcedureState.PROCEDURE_HALTED))
            else:
                self._halted.clear()
            self._current_proc = proc_type

    def reset_completion_flag(self):
        self._halted.clear()

    async def wait_till_procedure_halted(self):
        await self._halted.wait()