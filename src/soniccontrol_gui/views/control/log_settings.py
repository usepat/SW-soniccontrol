import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
import asyncio
from typing import Callable, List
from async_tkinter_loop import async_handler
from soniccontrol.logger.logger_discovery import AbstractLogger, LoggerDiscovery, Loglevel
from soniccontrol.sonic_device import CommandExecutionError, CommandValidationError
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.view import TabView, View
from soniccontrol_gui.widgets.message_box import MessageBox
from soniccontrol_gui.resources import images
from soniccontrol_gui.constants import sizes, ui_labels



class LoggerEntry(UIComponent):
    def __init__(self, parent: UIComponent, slot: View, logger: AbstractLogger):
        self._logger_instance = logger
        self._view = LoggerEntryView(slot, self._logger_instance.qual_logger_name)
        super().__init__(parent, self._view)

        self._view.selected_log_level = self._logger_instance.log_level
        self._view.set_log_level_selected_command(self._on_change_log_level)

    @async_handler
    async def _on_change_log_level(self):
        try:
            await self._logger_instance.set_log_level(self._view.selected_log_level)
        except (CommandExecutionError, CommandValidationError) as e:
            self._view.selected_log_level = self._logger_instance.log_level # log level could not be set, reverse it
            MessageBox.show_error(self._view.root, str(e))
            

class LoggerEntryView(View):
    def __init__(self, master: ttk.Window,  logger_name: str, *args, **kwargs) -> None:
        self._logger_name = logger_name
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        self._logger_name_label = ttk.Label(self, text=self._logger_name)
        self._selected_log_level: ttk.StringVar = ttk.StringVar()
        self._log_level_entry = ttk.Combobox(
            self, textvariable=self._selected_log_level, style=ttk.DARK, width=16
        )
        self._log_level_entry["state"] = "readonly" # prevents writing a value
        self._log_level_entry["values"] = [ level.name for level in Loglevel ]

    def _initialize_publish(self) -> None:
        self.pack(fill=ttk.X, side=ttk.TOP, pady=sizes.SMALL_PADDING)

        self.grid_columnconfigure(0, weight=1)  
        self.grid_columnconfigure(1, weight=0) 

        self._logger_name_label.grid(column=0, row=0, sticky=ttk.EW)
        self._log_level_entry.grid(column=1, row=0, sticky=ttk.E)

    @property
    def selected_log_level(self) -> Loglevel:
        return Loglevel[self._selected_log_level.get()]

    @selected_log_level.setter
    def selected_log_level(self, log_level: Loglevel):
        self._selected_log_level.set(log_level.name)

    def set_log_level_selected_command(self, command: Callable[[], None]) -> None:
        self._log_level_entry.bind("<<ComboboxSelected>>", lambda _: command())



class LogSettingsTab(UIComponent):
    def __init__(self, parent: UIComponent, logger_discovery: LoggerDiscovery):
        self._logger_discovery = logger_discovery
        self._view = LogSettingsTabView(parent.view)
        super().__init__(parent, self._view)

        self._lock = asyncio.Lock()
        self._logger_entries: List[LoggerEntry] = []
        
        self.top_level_window.pass_loading_task(self._reload_loggers())

        self._view.set_reload_loggers_command(async_handler(self._reload_loggers))

    async def _reload_loggers(self):
        async with self._lock:
            # destroy previous log entries
            for logger_entry in self._logger_entries:
                logger_entry.view.destroy()

            loggers = await self._logger_discovery.discover_loggers()
            self._logger_entries = [
                LoggerEntry(self, self._view.logger_slot, logger)
                for logger in loggers
            ]

    
class LogSettingsTabView(TabView):
    def __init__(self, master: ttk.Window, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    @property
    def image(self) -> ttk.ImageTk.PhotoImage:
        return ImageLoader.load_image_resource(images.CONSOLE_ICON_BLACK, sizes.TAB_ICON_SIZE)

    @property
    def tab_title(self) -> str:
        return ui_labels.LOGS_LABEL
    
    def _initialize_children(self) -> None:
        self._main_frame = ttk.Frame(self)
        self._reload_loggers_btn = ttk.Button(self._main_frame, text=ui_labels.RELOAD_LOGGERS)
        self._horizontal_scrolled_frame: ScrolledFrame = ScrolledFrame(
            self._main_frame, autohide=True
        )
        self._logger_slot = ttk.Frame(self._horizontal_scrolled_frame)

    def _initialize_publish(self) -> None:
        self._main_frame.pack(expand=True, fill=ttk.BOTH)
        self._reload_loggers_btn.pack(fill=ttk.X, padx=sizes.MEDIUM_PADDING, pady=sizes.MEDIUM_PADDING)
        self._horizontal_scrolled_frame.pack(
            expand=True, 
            fill=ttk.BOTH,
            pady=sizes.MEDIUM_PADDING,
            padx=sizes.MEDIUM_PADDING
        )
        self._logger_slot.pack(
            fill=ttk.X, side=ttk.TOP,
            pady=sizes.MEDIUM_PADDING,
            padx=sizes.MEDIUM_PADDING
        )

    @property
    def logger_slot(self) -> View:
        return self._logger_slot #type: ignore

    def set_reload_loggers_command(self, command: Callable[[], None]):
        self._reload_loggers_btn.configure(command=command)
