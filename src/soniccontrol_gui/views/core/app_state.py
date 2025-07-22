from enum import Enum
import logging
import attrs

from soniccontrol.events import EventManager, PropertyChangeEvent


class ExecutionState(Enum):
    NOT_RESPONSIVE = 0
    IDLE = 1
    BUSY = 2


attrs.define(init=True)
class AppExecutionContext:
    execution_state: ExecutionState
    running_task: str | None

    def __init__(self, execution_state: ExecutionState, running_task: str | None):
        self.execution_state = execution_state
        self.running_task = running_task


class AppState(EventManager):
    APP_EXECUTION_CONTEXT_PROP_NAME = "app_execution_context"

    def __init__(self, logger: logging.Logger):
        super().__init__()
        self._app_execution_context = AppExecutionContext(ExecutionState.IDLE, None)
        self._logger = logging.getLogger(logger.name + "." + AppState.__name__)

    @property
    def execution_state(self) -> ExecutionState:
        return self._app_execution_context.execution_state
    
    @property
    def running_task(self) -> str | None:
        return self._app_execution_context.running_task

    @property
    def app_execution_context(self) -> AppExecutionContext:
        return self._app_execution_context

    @app_execution_context.setter
    def app_execution_context(self, val: AppExecutionContext) -> None:
        old_val = self._app_execution_context
        self._app_execution_context = val
        if old_val != val:
            self._logger.debug("Execution state changed to: %s",self.execution_state.name)
            self.emit(PropertyChangeEvent(AppState.APP_EXECUTION_CONTEXT_PROP_NAME, old_val, val))

