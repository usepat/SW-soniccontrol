import asyncio
from soniccontrol.procedures.procedure import ProcedureType


class RemoteProcedureState:
    def __init__(self):
        self._current_proc: ProcedureType | None = None
        self._halted: asyncio.Event = asyncio.Event()

    def update(self, proc_type: ProcedureType | None):
        if proc_type != self._current_proc:
            if proc_type is None:
                # When no proc is running, than the procedure halted
                self._halted.set()
            else:
                self._halted.clear()
            self._current_proc = proc_type

    def reset_completion_flag(self):
        self._halted.clear()

    async def wait_till_procedure_halted(self):
        await self._halted.wait()