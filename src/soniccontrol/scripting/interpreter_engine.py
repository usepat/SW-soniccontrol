import asyncio
from enum import Enum
import logging
from typing import Iterable, Optional

import attrs
from soniccontrol.events import Event, EventManager, PropertyChangeEvent
from soniccontrol.scripting.scripting_facade import ExecutionStep, RunnableScript, ScriptException
from soniccontrol.procedures.procedure_controller import ProcedureController
from soniccontrol.sonic_device import SonicDevice
from soniccontrol.updater import Updater



class InterpreterState(Enum):
    READY = 0
    PAUSED = 1
    RUNNING = 2


@attrs.define()
class CurrentTarget:
    line: Optional[int] = attrs.field()
    task: str = attrs.field()

    @staticmethod
    def default():
        return CurrentTarget(line=None, task="Idle")

class InterpreterEngine(EventManager):
    INTERPRETATION_ERROR = "<<INTERPRETATION_ERROR>>"
    PROPERTY_INTERPRETER_STATE = "interpreter_state"
    PROPERTY_CURRENT_TARGET = "current_target"

    def __init__(self, device: SonicDevice, updater: Updater, logger: logging.Logger = logging.getLogger()):
        super().__init__()
        self._interpreter_worker = None
        self._device = device
        self._proc_controller = ProcedureController(device, updater, logger)
        self._script: Optional[RunnableScript] = None
        self._execution_steps: Iterable[ExecutionStep] | None = None
        self._interpreter_state = InterpreterState.READY
        self._halted = asyncio.Event()
        self._current_target = CurrentTarget.default()
        self._logger = logging.getLogger(logger.name + "." + InterpreterEngine.__name__)

    @property
    def interpreter_state(self) -> InterpreterState:
        return self._interpreter_state

    def _set_interpreter_state(self, state: InterpreterState):
        old_val = self._interpreter_state
        self._interpreter_state = state
        if state == InterpreterState.RUNNING:
            self._halted.clear()
        else:
            self._halted.set()
        if old_val != state:
            self.emit(PropertyChangeEvent(InterpreterEngine.PROPERTY_INTERPRETER_STATE, old_val, self._interpreter_state))

    def _set_current_target(self, target: CurrentTarget):
        old_val = self._current_target
        self._current_target = target
        if old_val != target:
            self.emit(PropertyChangeEvent(InterpreterEngine.PROPERTY_CURRENT_TARGET, old_val, self._current_target))

    async def wait_for_script_to_halt(self):
        if self._interpreter_state != InterpreterState.RUNNING:
            return
        await self._halted.wait()

    @property
    def script(self) -> Optional[RunnableScript]:
        return self._script
    
    @script.setter
    def script(self, script: Optional[RunnableScript]) -> None:
        self._script = script     

    def start(self):
        self._logger.info("Start script")
        assert self._interpreter_state != InterpreterState.RUNNING
        assert self._script is not None
        if self._execution_steps is None:
            self._execution_steps = iter(self._script)
        
        self._set_interpreter_state(InterpreterState.RUNNING)
        self._interpreter_worker = asyncio.create_task(self._interpreter_engine(single_instruction=False))

    def single_step(self):
        self._logger.info("Start script")
        assert self._interpreter_state != InterpreterState.RUNNING
        assert self._script is not None
        if self._execution_steps is None:
            self._execution_steps = iter(self._script)

        self._set_interpreter_state(InterpreterState.RUNNING)
        self._interpreter_worker = asyncio.create_task(self._interpreter_engine(single_instruction=True))

    async def stop(self):
        self._logger.info("Stop script")
        assert self._interpreter_state != InterpreterState.READY

        if self._interpreter_worker and not self._interpreter_worker.done() and not self._interpreter_worker.cancelled():
            self._interpreter_worker.cancel()
            await self._interpreter_worker
        
        self._execution_steps = None
        self._set_current_target(CurrentTarget.default())
        self._set_interpreter_state(InterpreterState.READY)

    async def pause(self):
        self._logger.info("Pause script")
        assert self._interpreter_state == InterpreterState.RUNNING

        if self._interpreter_worker and not self._interpreter_worker.done() and not self._interpreter_worker.cancelled():
            self._interpreter_worker.cancel()
            await self._interpreter_worker
        
        self._set_interpreter_state(InterpreterState.PAUSED)

    async def _interpreter_engine(self, single_instruction: bool = False):
        assert self._script is not None
        assert self._execution_steps is not None
        
        try:
            while True:
                step = next(self._execution_steps)
                self._set_current_target(CurrentTarget(step.line, step.description))
                self._logger.info("Current task: %s", step.description)
                await step.command(self._device, self._proc_controller)
                if single_instruction:
                    self._set_interpreter_state(InterpreterState.PAUSED)
                    break
        except StopIteration:
            self._execution_steps = None
            self._logger.info("Interpreter finished executing script")
            self._set_interpreter_state(InterpreterState.READY)
            self._set_current_target(CurrentTarget.default())
        except asyncio.CancelledError:
            self._logger.info("Interpreter got paused, while executing a script")
            self._set_interpreter_state(InterpreterState.PAUSED)
        except (ScriptException, Exception) as e:
            if not isinstance(e, ScriptException):
                e = ScriptException(str(e), line_begin=self._current_target.line, col_begin=0) # type:ignore line should be int and not None 
            self._logger.error(e)
            self._execution_steps = None
            self._set_interpreter_state(InterpreterState.READY)
            self._set_current_target(CurrentTarget.default())
            self.emit(Event(InterpreterEngine.INTERPRETATION_ERROR, exception=e))   
        


