from enum import Enum, auto
import logging
from typing import Any, Dict, Iterable, List
from async_tkinter_loop import async_handler

import matplotlib.figure
from soniccontrol.app_config import PLATFORM, SOFTWARE_VERSION
from soniccontrol.data_capturing.capture_target import CaptureTarget, CaptureTargets
from soniccontrol.data_capturing.experiment import Experiment, ExperimentMetaData
from soniccontrol.device_data import FirmwareInfo
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import TabView, View
import tkinter as tk
import ttkbootstrap as ttk
import matplotlib

from soniccontrol_gui.views.measure.experiment_form import ExperimentForm
from soniccontrol_gui.widgets.message_box import MessageBox
from soniccontrol_gui.widgets.notebook import Notebook
from soniccontrol.data_capturing.capture import Capture
from soniccontrol_gui.views.measure.csv_table import CsvTable
matplotlib.use("TkAgg")

from soniccontrol_gui.constants import sizes, ui_labels
from soniccontrol_gui.resources import images
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.views.measure.plotting import Plotting
from soniccontrol_gui.utils.plotlib.plot_builder import PlotBuilder


class ExperimentExecutionState(Enum):
    FILL_IN_METADATA = 0
    CHOOSE_CAPTURE_TARGET = auto()
    READY = auto()
    CAPTURING = auto()
    FINISHED = auto()

class Measuring(UIComponent):
    def __init__(self, parent: UIComponent, capture: Capture, capture_targets: Dict[CaptureTargets, CaptureTarget], firmware_info: FirmwareInfo):
        self._logger = logging.getLogger(parent.logger.name + "." + Measuring.__name__)

        self._logger.debug("Create SonicMeasure")
        self._experiment_execution_state = ExperimentExecutionState.FINISHED
        self._selected_target: CaptureTargets = CaptureTargets.FREE 
        self._capture = capture # TODO: move this to device window
        self._capture_targets = capture_targets
        self._firmware_info = firmware_info

        self._view = MeasuringView(parent.view)
        super().__init__(parent, self._view, self._logger)


        self._experiment_form = ExperimentForm(
            self,
            self._view._metadata_form_frame
        )
        self._experiment_form.subscribe(ExperimentForm.FINISHED_EDITING_EVENT, 
                                        lambda e: self._on_metadata_filled_in(e.data["experiment_metadata"]))

        self._time_figure = matplotlib.figure.Figure(dpi=100)
        self._time_subplot = self._time_figure.add_subplot(1, 1, 1)
        self._timeplot = PlotBuilder.create_timeplot_fuip(self._time_subplot)
        self._timeplottab = Plotting(self, self._timeplot)

        self._spectral_figure = matplotlib.figure.Figure(dpi=100)
        self._spectral_subplot = self._spectral_figure.add_subplot(1, 1, 1)
        self._spectralplot = PlotBuilder.create_spectralplot_uip(self._spectral_subplot)
        self._spectralplottab = Plotting(self, self._spectralplot)
        
        self._csv_table = CsvTable(self)

        self._view.set_target_selected_command(self._on_continue_select_target)
        self._view.add_tabs({
            ui_labels.LIVE_PLOT: self._timeplottab.view, 
            ui_labels.SONIC_MEASURE_LABEL: self._spectralplottab.view, 
            ui_labels.CSV_TAB_TITLE: self._csv_table.view
        })
        target_strs = map(lambda k: k.value, self._capture_targets.keys())
        self._view.set_target_combobox_items(target_strs)

        self._capture.data_provider.subscribe_property_listener(
            "data", lambda e: self._timeplot.update_data(e.new_value))
        # self._capture.data_provider.subscribe_property_listener(
        #     "data", lambda e: self._spectralplot.update_data(e.new_value))
        self._capture.data_provider.subscribe_property_listener(
            "data", lambda e: self._csv_table.on_update_data(e.new_value))

        self._capture.subscribe(Capture.START_CAPTURE_EVENT, 
                                lambda _e: setattr(self, "experiment_execution_state", ExperimentExecutionState.CAPTURING))
        self._capture.subscribe(Capture.END_CAPTURE_EVENT, 
                                lambda _e: setattr(self, "experiment_execution_state", ExperimentExecutionState.FINISHED))

        self.experiment_execution_state = ExperimentExecutionState.FINISHED

    @property
    def experiment_execution_state(self) -> ExperimentExecutionState:
        return self._experiment_execution_state
    
    @experiment_execution_state.setter
    def experiment_execution_state(self, v: ExperimentExecutionState) -> None:
        self._experiment_execution_state = v
        
        self._view.set_metadata_form_frame_visibility(False)
        self._view.set_choose_target_frame_visibility(False)
        self._view.set_capture_frame_visibility(False)
        match self._experiment_execution_state:
            case ExperimentExecutionState.FILL_IN_METADATA:
                self._view.set_metadata_form_frame_visibility(True)
            case ExperimentExecutionState.CHOOSE_CAPTURE_TARGET:
                self._view.set_choose_target_frame_visibility(True)
            case ExperimentExecutionState.READY:
                self._view.set_capture_frame_visibility(True)
                self._view.set_capture_button_label(ui_labels.START_CAPTURE)
                self._view.set_capture_button_command(self._on_start_capture)
            case ExperimentExecutionState.CAPTURING:
                self._view.set_capture_frame_visibility(True)
                self._view.set_capture_button_label(ui_labels.END_CAPTURE)
                self._view.set_capture_button_command(self._on_stop_capture)
            case ExperimentExecutionState.FINISHED:
                self._view.set_capture_frame_visibility(True)
                self._view.set_capture_button_label(ui_labels.NEW_EXPERIMENT)
                self._view.set_capture_button_command(self._on_new_experiment)

    def _on_new_experiment(self):
        self.experiment_execution_state = ExperimentExecutionState.FILL_IN_METADATA

    def _on_metadata_filled_in(self, metadata: ExperimentMetaData):
        self._experiment_metadata = metadata
        self.experiment_execution_state = ExperimentExecutionState.CHOOSE_CAPTURE_TARGET

    def _on_continue_select_target(self):
        target_str = self._view.selected_target
        self._selected_target = CaptureTargets(target_str)

        self.experiment_execution_state = ExperimentExecutionState.READY

    @async_handler
    async def _on_start_capture(self):
        assert (hasattr(self, "_experiment_metadata"))

        experiment = Experiment(
            metadata=self._experiment_metadata, firmware_info=self._firmware_info, 
            sonic_control_version=SOFTWARE_VERSION, operating_system=PLATFORM.value,
            capture_target=self._selected_target
        )
        try:
            target = self._capture_targets[self._selected_target]
            await self._capture.start_capture(experiment, target)
        except Exception as e:
            MessageBox.show_error(self._view.root, f"{e.__class__.__name__}: {str(e)}")

         # The execution state gets set as callback for capture. This is needed, because a capture can end automatically (Procedure finished for example)

    @async_handler
    async def _on_stop_capture(self):
        await self._capture.end_capture()

        # The execution state gets set as callback for capture. This is needed, because a capture can end automatically (Procedure finished for example)

        
class MeasuringView(TabView):
    def __init__(self, master: ttk.Window, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        tab_name = "measuring"
        self._main_frame: ttk.Frame = ttk.Frame(self)
        
        self._metadata_form_frame = ttk.Frame(self._main_frame)
        self._choose_target_frame = ttk.Frame(self._main_frame)
        self._capture_frame: ttk.Frame = ttk.Frame(self._main_frame)

        self._choose_target_label = ttk.Label(self._choose_target_frame, text=ui_labels.CHOOSE_A_CAPTURE_TARGET)
        self._selected_target_var = ttk.StringVar()
        self._target_combobox = ttk.Combobox(
            self._choose_target_frame, 
            textvariable=self._selected_target_var,
            state="readonly"
        )
        self._selected_target_button = ttk.Button(self._choose_target_frame, text=ui_labels.SELECTED)
        WidgetRegistry.register_widget(self._target_combobox, "target_combobox", tab_name)
        WidgetRegistry.register_widget(self._selected_target_button, "selected_target_button", tab_name)

        self._capture_btn_text = tk.StringVar()
        self._capture_btn: ttk.Button = ttk.Button(
            self._capture_frame,
            textvariable=self._capture_btn_text
        )
        self._notebook: Notebook = Notebook(self._capture_frame, "measuring")
        WidgetRegistry.register_widget(self._capture_btn, "capture_button", tab_name)



    def _initialize_publish(self) -> None:
        self._main_frame.pack(expand=True, fill=ttk.BOTH)
        
        self._metadata_form_frame.pack(fill=ttk.BOTH, padx=3, pady=3)
        self._metadata_form_frame.pack_forget()

        self._choose_target_frame.pack(fill=ttk.BOTH, padx=3, pady=3)
        self._choose_target_label.pack(fill=ttk.X)
        self._target_combobox.pack(fill=ttk.X)
        self._selected_target_button.pack(fill=ttk.X)
        self._choose_target_frame.pack_forget()

        self._capture_frame.pack(fill=ttk.BOTH, padx=3, pady=3)
        self._capture_btn.pack(fill=ttk.X, padx=sizes.SMALL_PADDING)
        self._notebook.pack(expand=True, fill=ttk.BOTH)
        self._capture_frame.pack_forget()

    @property
    def image(self) -> ttk.ImageTk.PhotoImage:
        return ImageLoader.load_image_resource(images.LINECHART_ICON_BLACK, sizes.TAB_ICON_SIZE)
    
    @property
    def tab_title(self) -> str:
        return ui_labels.SONIC_MEASURE_LABEL

    def add_tabs(self, tabs: Dict[str, View]) -> None:
        for (title, tabview) in tabs.items():
            self._notebook.add(tabview, text=title)

    def set_metadata_form_frame_visibility(self, is_visible: bool) -> None:
        if is_visible:
            self._metadata_form_frame.pack(expand=True, fill=ttk.BOTH)
        else: 
            self._metadata_form_frame.pack_forget()

    def set_choose_target_frame_visibility(self, is_visible: bool) -> None:
        if is_visible:
            self._choose_target_frame.pack(expand=True, fill=ttk.BOTH)
        else: 
            self._choose_target_frame.pack_forget()

    def set_capture_frame_visibility(self, is_visible: bool) -> None:
        if is_visible:
            self._capture_frame.pack(expand=True, fill=ttk.BOTH)
        else: 
            self._capture_frame.pack_forget()

    def set_capture_button_label(self, label: str):
        self._capture_btn_text.set(label)

    def set_capture_button_command(self, command):
        self._capture_btn.configure(command=command)

    def set_target_selected_command(self, command):
        self._selected_target_button.configure(command=command)
    
    @property
    def selected_target(self) -> str:
        return self._selected_target_var.get()
    
    def set_target_combobox_items(self, items: Iterable[str] | List[str]) -> None:
        if not isinstance(items, list):
            items = list(items)
            
        self._target_combobox["values"] = items
        self._selected_target_var.set(items[0])
    
    @property
    def metadata_form_frame(self) -> ttk.Frame:
        return self._metadata_form_frame


