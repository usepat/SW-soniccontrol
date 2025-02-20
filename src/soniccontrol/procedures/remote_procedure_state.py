import asyncio
from soniccontrol.procedures.procedure import ProcedureType


class RemoteProcedureState:
    def __init__(self):
        self._current_proc: ProcedureType | None = None
        self._completed: asyncio.Event = asyncio.Event()

    def update(self, proc_type: ProcedureType | None):
        if proc_type != self._current_proc:
            if self._current_proc is not None: # if change from None to Proc, it started the procedure, instead of completing it
                self._completed.set()
            self._current_proc = proc_type

    def reset_completion_flag(self):
        self._completed.clear()

    async def wait_till_procedure_completed(self):
        await self._completed.wait()