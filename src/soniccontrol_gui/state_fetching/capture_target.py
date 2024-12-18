
import abc
from enum import Enum
from typing import Any
from soniccontrol_gui.state_fetching.spectrum_measure import SpectrumMeasure, SpectrumMeasureArgs, SpectrumMeasureModel
from soniccontrol_gui.state_fetching.updater import Updater
from soniccontrol_gui.views.control.editor import ScriptFile
from soniccontrol_gui.views.control.proc_controlling import ProcControllingModel
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

    @abc.abstractmethod
    async def before_start_capture(self) -> None: ...

    @abc.abstractmethod
    def run_to_capturing_task(self) -> None: ...

    @abc.abstractmethod
    async def after_end_capture(self) -> None: ...


class CaptureFree(CaptureTarget):
    def __init__(self):
        super().__init__()

    async def before_start_capture(self) -> None:
        # nothing needed
        pass

    def run_to_capturing_task(self) -> None:
        # nothing needed
        pass

    async def after_end_capture(self) -> None:
        # nothing needed
        pass


class CaptureScript(CaptureTarget):
    def __init__(self, script_file: ScriptFile, scripting_facade: ScriptingFacade, interpreter_engine: InterpreterEngine):
        super().__init__()
        self._script_file = script_file
        self._interpreter_engine = interpreter_engine
        self._scripting_facade = scripting_facade
        self._is_capturing = False
        self._interpreter_engine.subscribe_property_listener(
            InterpreterEngine.PROPERTY_INTERPRETER_STATE, 
            self._complete_on_script_finish
        )

    def _complete_on_script_finish(self, _event: PropertyChangeEvent) -> None:
        if self._interpreter_engine.script is None:
            return
        
        if self._interpreter_engine.script.is_finished and self._is_capturing:
            self.emit(Event(CaptureTarget.COMPLETED_EVENT))

    async def before_start_capture(self) -> None:
        text = self._script_file.text
        script = self._scripting_facade.parse_script(text)
        self._interpreter_engine.script = script
        self._is_capturing = True

    def run_to_capturing_task(self) -> None:
        self._interpreter_engine.start()

    async def after_end_capture(self) -> None:
        self._is_capturing = False
        if self._interpreter_engine.interpreter_state == InterpreterState.RUNNING:
            await self._interpreter_engine.stop()


class CaptureProcedure(CaptureTarget):
    def __init__(self, procedure_controller: ProcedureController, proc_model: ProcControllingModel):
        super().__init__()
        self._procedure_controller = procedure_controller
        self._proc_model = proc_model
        self._args: Any | None = None
        self._is_capturing = False
        self._procedure_controller.subscribe(
            ProcedureController.PROCEDURE_STOPPED, 
            self._notify_on_procedure_finished
        )

    def _notify_on_procedure_finished(self, _e: Event):
        if not self._is_capturing:
            return
        
        self.emit(Event(CaptureTarget.COMPLETED_EVENT))

    async def before_start_capture(self) -> None:
        selected_proc = self._proc_model.selected_procedure
        proc_class = self._procedure_controller.proc_args_list[selected_proc]
        proc_args = self._proc_model.selected_procedure_args
        self._args = proc_class(**proc_args)
        self._is_capturing = True

    def run_to_capturing_task(self) -> None:
        assert self._args is not None
        self._procedure_controller.execute_proc(self._proc_model.selected_procedure, self._args)

    async def after_end_capture(self) -> None:
        self._is_capturing = False
        if self._procedure_controller.is_proc_running:
            await self._procedure_controller.stop_proc()


class CaptureSpectrumMeasure(CaptureTarget):
    def __init__(self, updater: Updater, procedure_controller: ProcedureController, spectrum_measure_model: SpectrumMeasureModel):
        super().__init__()
        self._updater = updater
        self._procedure_controller = procedure_controller
        self._spectrum_measure_model = spectrum_measure_model
        self._spectrum_measure = SpectrumMeasure(self._updater)
        self._args: SpectrumMeasureArgs | None = None
        self._is_capturing = False
        self._procedure_controller.subscribe(
            ProcedureController.PROCEDURE_STOPPED, 
            self._notify_on_procedure_finished
        )

    def _notify_on_procedure_finished(self, _e: Event):
        if not self._is_capturing:
            return
        
        self.emit(Event(CaptureTarget.COMPLETED_EVENT))

    async def before_start_capture(self) -> None:
        await self._updater.stop()
        proc_args = self._spectrum_measure_model.form_fields
        self._args = SpectrumMeasureArgs(**proc_args)
        self._is_capturing = True

    def run_to_capturing_task(self) -> None:
        assert self._args is not None
        self._procedure_controller.execute_procedure(self._spectrum_measure, ProcedureType.SPECTRUM_MEASURE, self._args)

    async def after_end_capture(self) -> None:
        self._is_capturing = False
        if self._procedure_controller.is_proc_running:
            await self._procedure_controller.stop_proc()
        self._updater.start()
        
