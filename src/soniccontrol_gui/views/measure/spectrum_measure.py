import logging
from typing import Any, Callable, Dict
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
from soniccontrol_gui.widgets.message_box import MessageBox


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
            "spectrum_measure",
            spectrum_measure_model.form_fields
        )
        self._view.set_guide_button_command(self._open_guide)

    def _open_guide(self):
        MessageBox(self._view.root, SpectrumMeasureArgs.get_description(), "Guide", [])


class SpectrumMeasureTabView(TabView):
    def __init__(self, master: ttk.Window, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        self._form_frame: ttk.Frame = ttk.Frame(self)
        self._help_frame: ttk.Frame = ttk.Frame(self)
        self._guide_button = ttk.Button(
            self._help_frame, 
            text=ui_labels.GUIDE_LABEL,
            style=ttk.INFO,
            image=ImageLoader.load_image_resource(images.INFO_ICON_WHITE, (13, 13)),
            compound=ttk.LEFT
        )

    def _initialize_publish(self) -> None:
        self._help_frame.pack(fill=ttk.X, side=ttk.BOTTOM)
        self._guide_button.pack(side=ttk.LEFT, padx=5)

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
    
    def set_guide_button_command(self, command: Callable[[], None]) -> None:
        self._guide_button.configure(command=command)
