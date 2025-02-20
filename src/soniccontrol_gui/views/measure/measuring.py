import logging
from typing import Any, Dict, Iterable, List
from async_tkinter_loop import async_handler
import attrs
import matplotlib.figure
from soniccontrol.data_capturing.capture_target import CaptureTarget, CaptureTargets
from soniccontrol.procedures.procs.spectrum_measure import SpectrumMeasure
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import TabView, View
import tkinter as tk
import ttkbootstrap as ttk
import matplotlib

from soniccontrol_gui.widgets.message_box import MessageBox
from soniccontrol_gui.widgets.notebook import Notebook
from soniccontrol_gui.widgets.procedure_widget import ProcedureWidget
from soniccontrol.data_capturing.capture import Capture
from soniccontrol_gui.views.measure.csv_table import CsvTable
matplotlib.use("TkAgg")

from soniccontrol_gui.constants import sizes, ui_labels
from soniccontrol_gui.resources import images
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.views.measure.plotting import Plotting
from soniccontrol_gui.utils.plotlib.plot_builder import PlotBuilder
from soniccontrol.data_capturing.capture_target import CaptureSpectrumArgs


@attrs.define()
class SpectrumMeasureModel(CaptureSpectrumArgs):
    form_fields: Dict[str, Any] = attrs.field(default={})

    @property
    def procedure_args(self) -> dict:
        return self.form_fields


class Measuring(UIComponent):
    def __init__(self, parent: UIComponent, capture: Capture, capture_targets: Dict[CaptureTargets, CaptureTarget], spectrum_measure_model: SpectrumMeasureModel):
        self._logger = logging.getLogger(parent.logger.name + "." + Measuring.__name__)

        self._logger.debug("Create SonicMeasure")
        self._capture = capture # TODO: move this to device window
        self._capture_targets = capture_targets
        
        self._view = MeasuringView(parent.view)
        super().__init__(parent, self._view, self._logger)

        self._time_figure = matplotlib.figure.Figure(dpi=100)
        self._time_subplot = self._time_figure.add_subplot(1, 1, 1)
        self._timeplot = PlotBuilder.create_timeplot_fuip(self._time_subplot)
        self._timeplottab = Plotting(self, self._timeplot)

        self._spectral_figure = matplotlib.figure.Figure(dpi=100)
        self._spectral_subplot = self._spectral_figure.add_subplot(1, 1, 1)
        self._spectralplot = PlotBuilder.create_spectralplot_uip(self._spectral_subplot)
        self._spectralplottab = Plotting(self, self._spectralplot)
        
        self._csv_table = CsvTable(self)

        
        self._spectrum_measure_widget = ProcedureWidget(
            self, 
            self._view.spectrum_measure_frame, 
            "Spectrum Measure", 
            SpectrumMeasure.get_args_class(),
            spectrum_measure_model.form_fields
        )

        self._view.set_capture_button_command(lambda: self._on_toggle_capture())
        self._view.set_capture_button_label(ui_labels.START_CAPTURE)
        self._view.add_tabs({
            ui_labels.LIVE_PLOT: self._timeplottab.view, 
            ui_labels.SONIC_MEASURE_LABEL: self._spectralplottab.view, 
            ui_labels.CSV_TAB_TITLE: self._csv_table.view
        })
        target_strs = map(lambda k: k.value, self._capture_targets.keys())
        self._view.set_target_combobox_items(target_strs)

        self._capture.data_provider.subscribe_property_listener("data", lambda e: self._timeplot.update_data(e.new_value))
        self._capture.data_provider.subscribe_property_listener("data", lambda e: self._spectralplot.update_data(e.new_value))
        self._capture.data_provider.subscribe_property_listener("data", lambda e: self._csv_table.on_update_data(e))

        self._capture.subscribe(Capture.START_CAPTURE_EVENT, lambda _e: self._view.set_capture_button_label(ui_labels.END_CAPTURE))
        self._capture.subscribe(Capture.END_CAPTURE_EVENT, lambda _e: self._view.set_capture_button_label(ui_labels.START_CAPTURE))

    @async_handler
    async def _on_toggle_capture(self):
        if self._capture.is_capturing:
            await self._capture.end_capture()
        else:
            try:
                target_str = self._view.selected_target
                if target_str == "": # return if empty
                    return
                target = self._capture_targets[CaptureTargets(target_str)]
                await self._capture.start_capture(target)
            except Exception as e:
                MessageBox.show_error(self._view.root, f"{e.__class__.__name__}: {str(e)}")
        

class MeasuringView(TabView):
    def __init__(self, master: ttk.Window, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        tab_name = "measuring"
        self._main_frame: ttk.Frame = ttk.Frame(self)
        
        self._capture_frame: ttk.Frame = ttk.Frame(self._main_frame)

        self._selected_target_var = ttk.StringVar()
        self._target_combobox = ttk.Combobox(
            self._main_frame, 
            textvariable=self._selected_target_var,
            state="readonly"
        )
        WidgetRegistry.register_widget(self._target_combobox, "target_combobox", tab_name)

        self._capture_btn_text = tk.StringVar()
        self._capture_btn: ttk.Button = ttk.Button(
            self._capture_frame,
            textvariable=self._capture_btn_text
        )
        WidgetRegistry.register_widget(self._capture_btn, "capture_button", tab_name)

        self._notebook: Notebook = Notebook(self._main_frame, "measuring")

        self._spectrum_measure_frame = ttk.Frame(self._main_frame)

    def _initialize_publish(self) -> None:
        self._main_frame.pack(expand=True, fill=ttk.BOTH)
        
        self._capture_frame.pack(fill=ttk.X, padx=3, pady=3)
        self._target_combobox.pack(fill=ttk.X, padx=sizes.SMALL_PADDING)
        self._capture_btn.pack(fill=ttk.X, padx=sizes.SMALL_PADDING)

        self._notebook.pack(expand=True, fill=ttk.BOTH)

        self._spectrum_measure_frame.pack(side=ttk.BOTTOM, fill=ttk.X, padx=3, pady=3)

    def add_tabs(self, tabs: Dict[str, View]) -> None:
        for (title, tabview) in tabs.items():
            self._notebook.add(tabview, text=title)

    def set_capture_button_label(self, label: str):
        self._capture_btn_text.set(label)

    def set_capture_button_command(self, command):
        self._capture_btn.configure(command=command)

    def set_target_combobox_items(self, items: Iterable[str] | List[str]) -> None:
        if not isinstance(items, list):
            items = list(items)
            
        self._target_combobox["values"] = items
        self._selected_target_var.set(items[0])

    @property
    def image(self) -> ttk.ImageTk.PhotoImage:
        return ImageLoader.load_image_resource(images.LINECHART_ICON_BLACK, sizes.TAB_ICON_SIZE)
    
    @property
    def tab_title(self) -> str:
        return ui_labels.SONIC_MEASURE_LABEL
    
    @property
    def selected_target(self) -> str:
        return self._selected_target_var.get()
    
    @property
    def spectrum_measure_frame(self) -> ttk.Frame:
        return self._spectrum_measure_frame


