
import abc
from enum import Enum
from typing import Any, Dict
import attrs
from soniccontrol.procedures.procs.spectrum_measure import SpectrumMeasure, SpectrumMeasureArgs
from soniccontrol.updater import Updater
from soniccontrol.events import Event, EventManager, PropertyChangeEvent
from soniccontrol.procedures.procedure import ProcedureType
from soniccontrol.procedures.procedure_controller import ProcedureController
from soniccontrol.scripting.interpreter_engine import InterpreterEngine, InterpreterState
from soniccontrol.scripting.scripting_facade import ScriptingFacade


class CaptureTargets(Enum):
    FREE = "Free"
    SCRIPT = "Script"
    PROCEDURE = "Procedure"
    SPECTRUM_MEASURE = "Spectrum Measure"


class CaptureTarget(abc.ABC, EventManager):
    COMPLETED_EVENT = "<<COMPLETED_EVENT>>"

    def __init__(self):
        super().__init__()

    @property
    @abc.abstractmethod
    def args(self) -> Dict[str, Any]: ...

    @abc.abstractmethod
    async def before_start_capture(self) -> None: ...

    @abc.abstractmethod
    def run_to_capturing_task(self) -> None: ...

    @abc.abstractmethod
    async def after_end_capture(self) -> None: ...


class CaptureFree(CaptureTarget):
    def __init__(self):
        super().__init__()

    @property
    def args(self) -> Dict[str, Any]: 
        return {}

    async def before_start_capture(self) -> None:
        # nothing needed
        pass

    def run_to_capturing_task(self) -> None:
        # nothing needed
        pass

    async def after_end_capture(self) -> None:
        # nothing needed
        pass


class CaptureScriptArgs:
    @property
    @abc.abstractmethod
    def script_text(self) -> str:
        ...

class CaptureScript(CaptureTarget):
    def __init__(self, script_args: CaptureScriptArgs, scripting_facade: ScriptingFacade, interpreter_engine: InterpreterEngine):
        super().__init__()
        self._script_args = script_args
        self._interpreter_engine = interpreter_engine
        self._scripting_facade = scripting_facade
        self._is_capturing = False
        self._interpreter_engine.subscribe_property_listener(
            InterpreterEngine.PROPERTY_INTERPRETER_STATE, 
            self._complete_on_script_finish
        )

    @property
    def args(self) -> Dict[str, Any]: 
        return { "script_text": self._script_args.script_text }

    def _complete_on_script_finish(self, _event: PropertyChangeEvent) -> None:
        if self._interpreter_engine.script is None:
            return
        
        # change to ready only happens if the script finished successfully
        if self._interpreter_engine.interpreter_state == InterpreterState.READY and self._is_capturing:
            self.emit(Event(CaptureTarget.COMPLETED_EVENT))

    async def before_start_capture(self) -> None:
        script_text = self._script_args.script_text
        script = self._scripting_facade.parse_script(script_text)
        self._interpreter_engine.script = script
        self._is_capturing = True

    def run_to_capturing_task(self) -> None:
        self._interpreter_engine.start()

    async def after_end_capture(self) -> None:
        self._is_capturing = False
        if self._interpreter_engine.interpreter_state == InterpreterState.RUNNING:
            await self._interpreter_engine.stop()


class CaptureProcedureArgs:
    @property
    @abc.abstractmethod
    def procedure_type(self) -> ProcedureType:
        ...

    @property
    @abc.abstractmethod
    def procedure_args(self) -> dict:
        ...

class CaptureProcedure(CaptureTarget):
    def __init__(self, procedure_controller: ProcedureController, proc_args: CaptureProcedureArgs):
        super().__init__()
        self._procedure_controller = procedure_controller
        self._selected_proc: ProcedureType | None = None
        self._args: Any | None = None
        self._is_capturing = False
        self._proc_args = proc_args
        self._procedure_controller.subscribe(
            ProcedureController.PROCEDURE_STOPPED, 
            self._notify_on_procedure_finished
        )

    @property
    def args(self) -> Dict[str, Any]: 
        return { 
            "procedure_type": self._proc_args.procedure_type,
            "procedure_args": self._proc_args.procedure_args
        }

    def _notify_on_procedure_finished(self, _e: Event):
        if not self._is_capturing:
            return
        
        self.emit(Event(CaptureTarget.COMPLETED_EVENT))

    async def before_start_capture(self) -> None:
        self._selected_proc = self._proc_args.procedure_type
        proc_class = self._procedure_controller.proc_args_list[self._selected_proc]
        self._args = proc_class(**self._proc_args.procedure_args)
        self._is_capturing = True

    def run_to_capturing_task(self) -> None:
        assert self._args is not None
        assert self._selected_proc
        self._procedure_controller.execute_proc(self._selected_proc, self._args)

    async def after_end_capture(self) -> None:
        self._is_capturing = False
        if self._procedure_controller.is_proc_running:
            await self._procedure_controller.stop_proc()


class CaptureSpectrumArgs:
    @property
    @abc.abstractmethod
    def spectrum_args(self) -> SpectrumMeasureArgs:
        ...

class CaptureSpectrumMeasure(CaptureTarget):
    def __init__(self, updater: Updater, procedure_controller: ProcedureController, spectrum_args: CaptureSpectrumArgs):
        super().__init__()
        self._updater = updater
        self._procedure_controller = procedure_controller
        self._spectrum_args = spectrum_args
        self._spectrum_measure = SpectrumMeasure(self._updater)
        self._args: SpectrumMeasureArgs | None = None
        self._is_capturing = False
        self._procedure_controller.subscribe(
            ProcedureController.PROCEDURE_STOPPED, 
            self._notify_on_procedure_finished
        )

    @property
    def args(self) -> Dict[str, Any]: 
        return { 
            "spectrum_args": attrs.asdict(self._spectrum_args.spectrum_args)
        }

    def _notify_on_procedure_finished(self, _e: Event):
        if not self._is_capturing:
            return
        
        self.emit(Event(CaptureTarget.COMPLETED_EVENT))

    async def before_start_capture(self) -> None:
        self._args = self._spectrum_args.spectrum_args
        await self._updater.stop()
        self._is_capturing = True

    def run_to_capturing_task(self) -> None:
        assert self._args is not None
        self._procedure_controller.execute_procedure(self._spectrum_measure, ProcedureType.SPECTRUM_MEASURE, self._args)

    async def after_end_capture(self) -> None:
        self._is_capturing = False
        if self._procedure_controller.is_proc_running:
            await self._procedure_controller.stop_proc()
        self._updater.start()
        
