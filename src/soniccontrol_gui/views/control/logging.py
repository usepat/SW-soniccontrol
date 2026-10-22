
from enum import Enum
import logging
from typing import Callable, Dict, List, Tuple

import attrs
from soniccontrol.logger.logger_discovery import DeviceLoggerDiscovery, PythonLoggerDiscovery
from soniccontrol.sonic_device import SonicDevice
from soniccontrol_gui import constants
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.file_explorer import open_file_explorer
from soniccontrol_gui.view import TabView, View
import ttkbootstrap as ttk

from soniccontrol_gui.views.control.log_settings import LogSettingsTab
from soniccontrol_gui.views.control.log_storage import DeviceLogFilter, LogStorage, NotDeviceLogFilter
from soniccontrol_gui.constants import sizes, ui_labels
from soniccontrol.utils.events import Event
from soniccontrol_gui.resources import images
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.utils.observable_list import ObservableList
from soniccontrol_gui.widgets.message_box import MessageBox
from soniccontrol_gui.widgets.notebook import Notebook



class Logging(UIComponent):
    def __init__(self, parent: UIComponent, connection_name: str, device: SonicDevice):
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

        app_logger_discovery = PythonLoggerDiscovery(self._logger)

        self._application_log_tab = LoggingTab(self, self._app_logStorage.logs)
        self._device_log_tab = LoggingTab(self, self._device_logStorage.logs)
        self._application_log_settings_tab = LogSettingsTab(self, app_logger_discovery)
        self._view.add_tabs({
            ui_labels.APP_LOGS_LABEL: self._application_log_tab.view,
            ui_labels.DEVICE_LOGS_LABEL: self._device_log_tab.view,
            ui_labels.APP_LOG_SETTINGS_LABEL: self._application_log_settings_tab.view,
        })

        device_logger_discovery = DeviceLoggerDiscovery(device)
        if device_logger_discovery.is_device_supporting_log_discovery():
            # FIXME: We need also to disable log discovery if app state is broken or idle
            self._device_log_settings_tab = LogSettingsTab(self, device_logger_discovery)
            self._view.add_tabs({
                ui_labels.DEVICE_LOG_SETTINGS_LABEL: self._device_log_settings_tab.view
            })

        self._view.set_open_logs_command(self._open_logs)

    def _open_logs(self):
        try:
            open_file_explorer(constants.files.LOG_DIR)
        except Exception as e:
            MessageBox.show_error(self._view.root, str(e))


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
        self._open_logs_button = ttk.Button(self, text=ui_labels.OPEN_LOGS)
        self._notebook: Notebook = Notebook(self, "logging")

    def _initialize_publish(self) -> None:
        self._open_logs_button.pack(fill=ttk.NONE, side=ttk.TOP)
        self._notebook.pack(expand=True, fill=ttk.BOTH)

    def add_tabs(self, tabs: Dict[str, View]) -> None:
        for (title, tabview) in tabs.items():
            self._notebook.add(tabview, text=title)

    def set_open_logs_command(self, command: Callable[[], None]) -> None:
        self._open_logs_button.configure(command=command)


class TagType(Enum):
    TIMESTAMP = "timestamp"
    LOGLEVEL = "loglevel"
    LOGGER = "logger"

@attrs.define()
class Tag:
    tag_type: TagType
    begin_line: int
    begin_col: int
    end_line: int
    end_col: int


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
            self._add_log_text(log)
        self._view.scroll_to_end()

    def _add_log(self, e: Event):
        self._add_log_text(e.data["item"])
        self._view.scroll_to_end()
       
    def _add_log_text(self, log_text: str):
        # insert text and get the start index of the inserted text in the Text widget
        start_line = self._view.append_text_line(log_text)

        # 2026-09-24 10:04:37,236: INFO - simulation.SerialCommunicator -
        timestamp_sep = ": "
        sep = " -"
        end_timestamp = log_text.index(timestamp_sep)
        begin_loglevel = end_timestamp + len(timestamp_sep)
        end_loglevel = log_text.index(sep, begin_loglevel)
        begin_logger_name = end_loglevel + len(sep)
        end_logger_name = log_text.index(sep, begin_logger_name)

        tags = [
            Tag(TagType.TIMESTAMP, start_line, 0, start_line, end_timestamp),
            Tag(TagType.LOGLEVEL, start_line, begin_loglevel, start_line, end_loglevel),
            Tag(TagType.LOGGER, start_line, begin_logger_name, start_line, end_logger_name),
        ]
        for tag in tags:
            self._view.add_tag(tag)

    def _remove_log(self, e: Event):
        log_text: str = e.data["item"]
        num_lines = log_text.count("\n") + 1
        # pop num_lines from beginning
        for _ in range(num_lines):
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

    @property
    def num_log_lines(self) -> int:
        result = self._text_widget.count("1.0", ttk.END, "lines")
        assert result is not None
        return result[0]

    def _initialize_children(self) -> None:
        self._main_frame: ttk.Frame = ttk.Frame(self)
        self._output_frame: ttk.Labelframe = ttk.Labelframe(
            self._main_frame, text=ui_labels.OUTPUT_LABEL
        )

        self._text_widget: ttk.Text = ttk.Text(
            self._output_frame, 
            font=("Consolas", 10)
        )
        self._text_widget.tag_configure(TagType.TIMESTAMP.value, foreground="blue")
        self._text_widget.tag_configure(TagType.LOGLEVEL.value, foreground="blue")
        self._text_widget.tag_configure(TagType.LOGGER.value, foreground="blue")
        self._scrollbar_y = ttk.Scrollbar(self._output_frame, orient="vertical", command=self._text_widget.yview)
        self._scrollbar_x = ttk.Scrollbar(self._output_frame, orient="horizontal", command=self._text_widget.xview)
        
        self._text_widget.configure(
            state=ttk.DISABLED,
            yscrollcommand=self._scrollbar_y.set,
            xscrollcommand=self._scrollbar_x.set
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
        self._output_frame.columnconfigure(0, weight=sizes.EXPAND)
        self._output_frame.columnconfigure(1, weight=sizes.DONT_EXPAND)
        self._output_frame.rowconfigure(0, weight=sizes.EXPAND)
        self._output_frame.rowconfigure(1, weight=sizes.DONT_EXPAND)
        self._text_widget.grid(
            row=0, column=0, sticky=ttk.NSEW
        )
        self._scrollbar_y.grid(row=0, column=1, sticky=ttk.NS)
        self._scrollbar_x.grid(row=1, column=0, sticky=ttk.EW)

    def append_text_line(self, text: str):
        self._text_widget.configure(state=ttk.NORMAL)
        start_index = self._text_widget.index("end-1c")
        self._text_widget.insert(ttk.END, text + "\n")
        self._text_widget.configure(state=ttk.DISABLED)
        return int(start_index.split(".")[0])

    def add_tag(self, tag: Tag):
        begin = f"{tag.begin_line}.{tag.begin_col}"
        end = f"{tag.end_line}.{tag.end_col}"

        self._text_widget.configure(state=ttk.NORMAL)
        self._text_widget.tag_add(tag.tag_type.value, begin, end)
        self._text_widget.configure(state=ttk.DISABLED)
        
    def scroll_to_end(self):
        self._text_widget.yview_moveto(1.0)

    def destroy_ith_text_line(self, i: int):
        text = self._text_widget.get("1.0", ttk.END)
        text_lines = text.splitlines(keepends=True)
        text_lines.pop(i)
        text = "".join(text_lines)

        self._text_widget.configure(state=ttk.NORMAL)
        self._text_widget.delete("1.0", ttk.END)
        self._text_widget.insert("1.0", text)
        self._text_widget.configure(state=ttk.DISABLED)
