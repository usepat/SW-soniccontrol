import logging
from typing import Any, Callable, Dict, Iterable

from async_tkinter_loop import async_handler
import attrs
from soniccontrol.data_capturing.capture_target import CaptureProcedureArgs
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import TabView, View
from soniccontrol.procedures.procedure_controller import ProcedureController, ProcedureType

import ttkbootstrap as ttk

from soniccontrol_gui.constants import sizes, ui_labels
from soniccontrol.events import Event, PropertyChangeEvent
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.views.core.app_state import AppState, ExecutionState
from soniccontrol_gui.widgets.message_box import MessageBox
from soniccontrol_gui.widgets.procedure_widget import ProcedureWidget
from soniccontrol_gui.resources import images



@attrs.define()
class ProcControllingModel(CaptureProcedureArgs):
    selected_procedure: ProcedureType = attrs.field(default=ProcedureType.RAMP)
    procedure_arg_dict: Dict[ProcedureType, dict] = attrs.field(default={})

    @property
    def procedure_type(self) -> ProcedureType:
        return self.selected_procedure

    @property
    def procedure_args(self) -> dict:
        return self.procedure_arg_dict[self.selected_procedure]


class ProcControlling(UIComponent):
    def __init__(self, parent: UIComponent, proc_controller: ProcedureController, model: ProcControllingModel, app_state: AppState):
        self._logger = logging.getLogger(parent.logger.name + "." + ProcControlling.__name__)

        self._model: ProcControllingModel = model
        self._logger.debug("Create ProcControlling")
        self._proc_controller = proc_controller
        self._app_state = app_state
        self._view = ProcControllingView(parent.view)
        self._proc_widgets: Dict[ProcedureType, ProcedureWidget] = {}
        super().__init__(parent, self._view, self._logger)
        self._add_proc_widgets()
        
        self._view.set_procedure_selected_command(self._on_proc_selected)
        self._view.set_start_button_command(self._on_run_pressed)
        self._view.set_stop_button_command(self._on_stop_pressed)
        self._proc_controller.subscribe(ProcedureController.PROCEDURE_RUNNING, self.on_procedure_running)
        self._proc_controller.subscribe(ProcedureController.PROCEDURE_STOPPED, self.on_procedure_stopped)
        self._app_state.subscribe_property_listener(AppState.EXECUTION_STATE_PROP_NAME, self._on_execution_state_changed)
        
        self.on_procedure_stopped(None) # type: ignore

    def _on_execution_state_changed(self, e: PropertyChangeEvent) -> None:
        execution_state: ExecutionState = e.new_value
        if execution_state == ExecutionState.BUSY_EXECUTING_PROCEDURE:
            return
        elif execution_state == ExecutionState.IDLE:
            self._view.set_start_button_enabled(True) 
        else:
            # user should not be able to start a procedure 
            # while flashing, a script running or a disconnect
            self._view.set_start_button_enabled(False)

    def _add_proc_widgets(self):
        for proc_type, args_class in self._proc_controller.proc_args_list.items():
            proc_dict = {}
            proc_widget = ProcedureWidget(
                self, self._view.procedure_frame, 
                proc_type.value, args_class, proc_dict,
            )
            proc_widget.view.hide()
            self._model.procedure_arg_dict[proc_type] = proc_dict
            self._proc_widgets[proc_type] = proc_widget
        proc_names = map(lambda proc_type: proc_type.value, self._proc_controller.proc_args_list.keys())
        self._view.set_procedure_combobox_items(proc_names)

    def _on_proc_selected(self):
        for proc_widget in self._proc_widgets.values():
            proc_widget.view.hide()
        self._model.selected_procedure = ProcedureType(self._view.selected_procedure)
        self._proc_widgets[self._model.selected_procedure].view.show()

    def _on_run_pressed(self):
        proc_args = self._proc_widgets[self._model.selected_procedure].get_args()
        if proc_args is not None:
            try:
                self._proc_controller.execute_proc(self._model.selected_procedure, proc_args)
            except Exception as e:
                self._logger.error(e)
                MessageBox.show_error(self._view.root, str(e))

    @async_handler
    async def _on_stop_pressed(self):
        await self._proc_controller.stop_proc()

    def on_procedure_running(self, e: Event):
        self._view.set_running_proc_label(ui_labels.PROC_RUNNING.format(e.data["proc_type"]))
        self._view.set_start_button_enabled(False)
        self._view.set_stop_button_enabled(True)
        self._app_state.execution_state = ExecutionState.BUSY_EXECUTING_PROCEDURE

    def on_procedure_stopped(self, _e: Event):
        self._view.set_running_proc_label(ui_labels.PROC_NOT_RUNNING)
        self._view.set_start_button_enabled(True)
        self._view.set_stop_button_enabled(False)
        self._app_state.execution_state = ExecutionState.IDLE

class ProcControllingView(TabView):
    def __init__(self, master: ttk.Frame | View, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

    @property
    def image(self) -> ttk.ImageTk.PhotoImage:
        return ImageLoader.load_image_resource(images.CONSOLE_ICON_BLACK, sizes.TAB_ICON_SIZE)

    @property
    def tab_title(self) -> str:
        return ui_labels.PROCEDURES_LABEL
    
    def _initialize_children(self) -> None:
        tab_name = "proc_controlling"
        self._selected_procedure_var = ttk.StringVar()
        self._procedure_combobox = ttk.Combobox(self, textvariable=self._selected_procedure_var)

        # Procedure widget placeholder
        self._procedure_widget_frame = ttk.Frame(self)

        # Control buttons
        self._controls_frame = ttk.Frame(self)
        self._start_button = ttk.Button(self._controls_frame, text=ui_labels.START_LABEL)
        self._stop_button = ttk.Button(self._controls_frame, text=ui_labels.STOP_LABEL)
        self._running_proc_label = ttk.Label(self._controls_frame, text="Status: Not running")

        WidgetRegistry.register_widget(self._procedure_combobox, "procedure_combobox", tab_name)
        WidgetRegistry.register_widget(self._start_button, "start_button", tab_name)
        WidgetRegistry.register_widget(self._stop_button, "stop_button", tab_name)
        WidgetRegistry.register_widget(self._running_proc_label, "running_proc_label", tab_name)

    def _initialize_publish(self) -> None:
        self._procedure_combobox.pack(fill=ttk.X, pady=5)
        self._procedure_widget_frame.pack(fill=ttk.BOTH, expand=True, pady=5)
        self._controls_frame.pack(fill=ttk.X, pady=5)
        self._start_button.pack(side=ttk.LEFT, padx=5)
        self._stop_button.pack(side=ttk.LEFT, padx=5)
        self._running_proc_label.pack(side=ttk.LEFT, fill=ttk.X, expand=True, padx=5)

    @property
    def procedure_frame(self) -> ttk.Frame:
        return self._procedure_widget_frame

    @property
    def selected_procedure(self) -> str:
        return self._selected_procedure_var.get()
    
    def set_running_proc_label(self, text: str) -> None:
        self._running_proc_label.configure(text=text)

    def set_procedure_combobox_items(self, items: Iterable[str]) -> None:
        self._procedure_combobox["values"] = list(items)

    def set_procedure_selected_command(self, command: Callable[[], None]) -> None:
        self._procedure_combobox.bind("<<ComboboxSelected>>", lambda _: command())

    def set_start_button_command(self, command: Callable[[], None]) -> None:
        self._start_button.configure(command=command)

    def set_stop_button_command(self, command: Callable[[], None]) -> None:
        self._stop_button.configure(command=command)

    def set_start_button_enabled(self, enabled: bool) -> None:
        self._start_button.configure(state=ttk.NORMAL if enabled else ttk.DISABLED)

    def set_stop_button_enabled(self, enabled: bool) -> None:
        self._stop_button.configure(state=ttk.NORMAL if enabled else ttk.DISABLED)
