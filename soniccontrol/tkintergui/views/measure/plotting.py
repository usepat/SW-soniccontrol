from soniccontrol.interfaces.mvc_command import MvcCommand
from soniccontrol.interfaces.ui_component import UIComponent
from soniccontrol.interfaces.view import View

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from typing import Callable, Dict

from soniccontrol.tkintergui.utils.constants import sizes, ui_labels
from soniccontrol.utils.plotlib.plot import Plot


class Plotting(UIComponent):
    def __init__(self, parent: UIComponent, plot: Plot):
        self._plot = plot
        self._figure: Figure = plot.plot.get_figure()
        self._view = PlottingView(parent.view, self._figure)
        super().__init__(parent, self._view)

        for (attrName, line) in self._plot.lines.items():
            self.view.add_line(attrName, line.get_label(), self.create_toggle_line_callback(attrName))
        self._view.update_plot()
    
        self._plot.subscribe_property_listener("plot", lambda _: self._view.update_plot())


    def create_toggle_line_callback(self, attrName: str):
            def toggle_line():
                is_visible = self._view.get_line_visibility(attrName)
                self._plot.toggle_line(attrName, is_visible)
            return toggle_line


class PlottingView(View):
    def __init__(self, master: tk.Widget, _figure: Figure, *args, **kwargs) -> None:
        self._figure = _figure
        super().__init__(master, *args, **kwargs)


    def _initialize_children(self) -> None:
        self._main_frame: ScrolledFrame = ScrolledFrame(self, autohide=True)
        self._plot_frame: ttk.Frame = ttk.Frame(self._main_frame)
        self._figure_canvas: FigureCanvasTkAgg = FigureCanvasTkAgg(
            self._figure, self._plot_frame
        )
        self._toolbar = NavigationToolbar2Tk(
            self._figure_canvas, self._plot_frame, pack_toolbar=False
        )
        self._toggle_button_frame: ttk.Frame = ttk.Frame(self)
        self._line_toggle_buttons: Dict[str, ttk.Checkbutton] = {}
        self._line_visibilities: Dict[str, tk.BooleanVar] = {}
        
        self._figure_canvas.draw()


    def _initialize_publish(self) -> None:
        self._main_frame.pack(expand=True, fill=ttk.BOTH, padx=3, pady=3)
        self._plot_frame.pack(padx=3, pady=3)

        self._toolbar.pack(side=ttk.BOTTOM, fill=ttk.X)
        self._figure_canvas.get_tk_widget().pack(fill=ttk.BOTH, expand=True)

        self._toggle_button_frame.pack(fill=ttk.X, padx=3, pady=3)


    def update_plot(self):
        self._figure_canvas.draw()
        self._figure_canvas.flush_events()

    def get_line_visibility(self, attrName: str) -> bool:
        return self._line_visibilities[attrName].get()

    def add_line(self, attrName: str, line_label: str, toggle_command: Callable[[], None]) -> None:
        self._line_visibilities[attrName] = tk.BooleanVar(value=True)
        toggle_button = ttk.Checkbutton(
            self._toggle_button_frame, 
            text=line_label, 
            variable=self._line_visibilities[attrName],
            command=toggle_command
        )
        toggle_button.grid(row=0, column=len(self._line_toggle_buttons), padx=sizes.SMALL_PADDING)
        self._line_toggle_buttons[attrName] = toggle_button
