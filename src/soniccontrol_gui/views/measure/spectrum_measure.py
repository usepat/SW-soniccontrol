import logging
from typing import Any, Dict
import attrs
import ttkbootstrap as ttk

from soniccontrol.data_capturing.capture_target import CaptureSpectrumArgs
from soniccontrol.procedures.procs.spectrum_measure import SpectrumMeasureArgs
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.view import TabView
from soniccontrol_gui.widgets.form_widget import FormWidget
from soniccontrol_gui.constants import sizes, ui_labels
from soniccontrol_gui.resources import images


@attrs.define()
class SpectrumMeasureModel(CaptureSpectrumArgs):
    form_fields: Dict[str, Any] = attrs.field(default={})

    @property
    def spectrum_args(self) -> SpectrumMeasureArgs:
        return SpectrumMeasureArgs(**self.form_fields)


class SpectrumMeasureTab(UIComponent):
    def __init__(self, parent: UIComponent, spectrum_measure_model: SpectrumMeasureModel):
        self._logger = logging.getLogger(parent.logger.name + "." + SpectrumMeasureTab.__name__)

        self._view = SpectrumMeasureTabView(parent.view) # type: ignore
        super().__init__(parent, self._view, self._logger)
        
        self._spectrum_measure_widget = FormWidget(
            self, 
            self._view.form_frame, 
            ui_labels.SPECTRUM_MEASURE_TITLE, 
            SpectrumMeasureArgs,
            spectrum_measure_model.form_fields
        )


class SpectrumMeasureTabView(TabView):
    def __init__(self, master: ttk.Window, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        self._form_frame: ttk.Frame = ttk.Frame(self)

    def _initialize_publish(self) -> None:
        self._form_frame.pack(expand=True, fill=ttk.BOTH)

    @property
    def image(self) -> ttk.ImageTk.PhotoImage:
        return ImageLoader.load_image_resource(images.LINECHART_ICON_BLACK, sizes.TAB_ICON_SIZE)
    
    @property
    def tab_title(self) -> str:
        return ui_labels.SPECTRUM_MEASURE_TITLE
    
    @property
    def form_frame(self) -> ttk.Frame:
        return self._form_frame
