from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.view import View

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from typing import Callable, Dict

from soniccontrol_gui.constants import sizes, ui_labels
from soniccontrol_gui.utils.plotlib.plot import Plot


class Plotting(UIComponent):
    def __init__(self, parent: UIComponent, plot: Plot, **kwargs):
        self._plot = plot
        self._figure: Figure = plot.plot.get_figure()
        self._view = PlottingView(parent.view, self._figure, **kwargs)
        super().__init__(parent, self._view)

        for (attrName, line) in self._plot.lines.items():
            self._view.add_line(attrName, line.get_label(), self.create_toggle_line_callback(attrName))
            
        self._plot.subscribe_property_listener("plot", lambda _: self._view.update_plot())


    def create_toggle_line_callback(self, attrName: str):
        def toggle_line():
            is_visible = self._view.get_line_visibility(attrName)
            self._plot.toggle_line(attrName, is_visible)
        return toggle_line
    
    def set_data_provider_size_change_callback(self, command: Callable[[int], None]) -> None:
        self._view.set_send_max_size_callback(command)


class PlottingView(View):
    def __init__(self, master: tk.Widget, _figure: Figure, *args, **kwargs) -> None:
        self._figure = _figure
        self._use_max_size_entry = kwargs.pop("max_size_editable", False)
        super().__init__(master, *args, **kwargs)
        self._callback: Callable[[bool], None] = lambda _: None

    def _initialize_children(self) -> None:
        self._main_frame: ScrolledFrame = ScrolledFrame(self, autohide=True)
        self._plot_frame: ttk.Frame = ttk.Frame(self._main_frame)
        self._figure_canvas: FigureCanvasTkAgg = FigureCanvasTkAgg(
            self._figure, self._plot_frame
        )
        self._toolbar = NavigationToolbar2Tk(
            self._figure_canvas, self, pack_toolbar=False
        )
        self._toggle_button_frame: ttk.Frame = ttk.Frame(self)
        self._line_toggle_buttons: Dict[str, ttk.Checkbutton] = {}
        self._line_visibilities: Dict[str, tk.BooleanVar] = {}
        
        self._plot_frame.bind('<Configure>', lambda _e: self.update_plot())
        self._figure_canvas.draw()
        if self._use_max_size_entry:
            self._max_size_var: ttk.StringVar = ttk.StringVar(value="")
            # Create a frame to hold label, entry, and button in a row
            self._max_size_row_frame = ttk.Frame(self)
            self._max_size_label = ttk.Label(self._max_size_row_frame, text="Change max plot size")
            self._max_size_entry = ttk.Entry(self._max_size_row_frame, textvariable=self._max_size_var, width=12)
            self._send_max_size_button = ttk.Button(self._max_size_row_frame, text=ui_labels.SEND_LABEL)
            


    def _initialize_publish(self) -> None:        
        # packing order is important because of expand attribute
        self._toolbar.pack(side=ttk.TOP, fill=ttk.X)
        self._toggle_button_frame.pack(side=ttk.BOTTOM, fill=ttk.NONE)
        if self._use_max_size_entry:
            # Pack label, entry, and button side by side in the row frame
            self._max_size_label.pack(side=ttk.LEFT, padx=(0, 4))
            self._max_size_entry.pack(side=ttk.LEFT, padx=(0, 4))
            self._send_max_size_button.pack(side=ttk.LEFT)
            self._max_size_row_frame.pack(side=ttk.BOTTOM, fill=ttk.NONE, pady=4)
        self._main_frame.pack(expand=True, fill=ttk.BOTH, padx=5, pady=5)
        self._plot_frame.pack(fill=ttk.BOTH, expand=True)
        self._figure_canvas.get_tk_widget().pack(fill=ttk.BOTH, expand=True)
        

    def update_plot(self):
        self._figure_canvas.draw_idle()
        self.root.update_idletasks() # do not call self._figure_canvas.flush_events() it is badly implemented and calls root.update()

    def get_line_visibility(self, attrName: str) -> bool:
        return self._line_visibilities[attrName].get()

    def add_line(self, attrName: str, line_label: str, toggle_command: Callable[[], None]) -> None:
        self._line_visibilities[attrName] = tk.BooleanVar(value=True)
        toggle_button = ttk.Checkbutton(
            self._toggle_button_frame, 
            text=line_label, 
            variable=self._line_visibilities[attrName],
            command=toggle_command,
            bootstyle="round-toggle"
        )
        toggle_button.grid(row=0, column=len(self._line_toggle_buttons), padx=sizes.SMALL_PADDING)
        self._line_toggle_buttons[attrName] = toggle_button

    def set_send_max_size_callback(self, command: Callable[[int], None]) -> None:
        assert self._use_max_size_entry, "Only set the callback if entry is being used"
        def on_send():
            try:
                value = int(self._max_size_var.get())
                command(value)
            except ValueError:
                pass  # Optionally handle invalid input here
        self._send_max_size_button.configure(command=on_send)
