
import logging
from typing import Dict
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.view import TabView, View
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame

from soniccontrol_gui.state_fetching.logger import DeviceLogFilter, LogStorage, NotDeviceLogFilter
from soniccontrol_gui.constants import sizes, ui_labels
from soniccontrol.events import Event
from soniccontrol_gui.resources import images
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.utils.observable_list import ObservableList
from soniccontrol_gui.widgets.notebook import Notebook


class Logging(UIComponent):
    def __init__(self, parent: UIComponent, connection_name: str):
        self._logger: logging.Logger = logging.getLogger(connection_name)
        self._view = LoggingView(parent.view)
        super().__init__(parent, self._view, self._logger)

        self._logger.debug("Create logStorage for storing logs")
        self._app_logStorage = LogStorage()
        app_log_storage_handler = self._app_logStorage.create_log_handler()
        self._logger.addHandler(app_log_storage_handler)
        not_device_log_filter = NotDeviceLogFilter()
        app_log_storage_handler.addFilter(not_device_log_filter)

        self._device_logStorage = LogStorage()
        device_log_storage_handler = self._device_logStorage.create_log_handler()
        self._logger.addHandler(device_log_storage_handler)
        device_log_filter = DeviceLogFilter()
        device_log_storage_handler.addFilter(device_log_filter)

        self._application_log_tab = LoggingTab(self, self._app_logStorage.logs)
        self._device_log_tab = LoggingTab(self, self._device_logStorage.logs)
        self._view.add_tabs({
            ui_labels.DEVICE_LOGS_LABEL: self._device_log_tab.view,
            ui_labels.APP_LOGS_LABEL: self._application_log_tab.view
        })


class LoggingView(TabView):
    def __init__(self, master: ttk.Window, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    @property
    def image(self) -> ttk.ImageTk.PhotoImage:
        return ImageLoader.load_image_resource(images.CONSOLE_ICON_BLACK, sizes.TAB_ICON_SIZE)

    @property
    def tab_title(self) -> str:
        return ui_labels.LOGS_LABEL
    
    def _initialize_children(self) -> None:
        self._notebook: Notebook = Notebook(self, "logging")

    def _initialize_publish(self) -> None:
        self._notebook.pack(expand=True, fill=ttk.BOTH)

    def add_tabs(self, tabs: Dict[str, View]) -> None:
        for (title, tabview) in tabs.items():
            self._notebook.add(tabview, text=title)


class LoggingTab(UIComponent):
    def __init__(self, parent: UIComponent, logs: ObservableList):
        self._logs = logs
        self._view = LoggingTabView(parent.view)
        super().__init__(parent, self._view)
        self._init_logs()
        self._logs.subscribe(ObservableList.EVENT_ITEM_ADDED, self._add_log)
        self._logs.subscribe(ObservableList.EVENT_ITEM_DELETED, self._remove_log)

    def _init_logs(self):
        for log in self._logs:
            self._view.append_text_line(log)

    def _add_log(self, e: Event):
        self._view.append_text_line(e.data["item"])

    def _remove_log(self, e: Event):
        self._view.destroy_ith_text_line(0)

class LoggingTabView(TabView):
    def __init__(self, master: ttk.Window, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    @property
    def image(self) -> ttk.ImageTk.PhotoImage:
        return ImageLoader.load_image_resource(images.CONSOLE_ICON_BLACK, sizes.TAB_ICON_SIZE)

    @property
    def tab_title(self) -> str:
        return ui_labels.LOGS_LABEL

    def _initialize_children(self) -> None:
        self._main_frame: ttk.Frame = ttk.Frame(self)
        self._output_frame: ttk.Labelframe = ttk.Labelframe(
            self._main_frame, text=ui_labels.OUTPUT_LABEL
        )
        self._scrolled_frame: ScrolledFrame = ScrolledFrame(
            self._output_frame, autohide=True
        )

    def _initialize_publish(self) -> None:
        self._main_frame.pack(expand=True, fill=ttk.BOTH)
        self._main_frame.columnconfigure(0, weight=sizes.EXPAND)
        self._main_frame.rowconfigure(0, weight=sizes.EXPAND)
        self._main_frame.rowconfigure(1, weight=sizes.DONT_EXPAND, minsize=40)
        self._output_frame.grid(
            row=0,
            column=0,
            sticky=ttk.NSEW,
            pady=sizes.MEDIUM_PADDING,
            padx=sizes.LARGE_PADDING,
        )
        self._scrolled_frame.pack(
            expand=True,
            fill=ttk.BOTH,
            pady=sizes.MEDIUM_PADDING,
            padx=sizes.MEDIUM_PADDING,
        )

    def append_text_line(self, text: str):
        ttk.Label(self._scrolled_frame, text=text, font=("Consolas", 10)).pack(
            fill=ttk.X, side=ttk.TOP, anchor=ttk.W
        )
        self._scrolled_frame.update()
        self._scrolled_frame.yview_moveto(1)

    def destroy_ith_text_line(self, i: int):
        child = self._scrolled_frame.winfo_children()[i]
        child.destroy()