
import asyncio
import logging
from pathlib import Path
from tkinter import filedialog
from typing import Callable, List, Iterable, Optional
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
import json
from sonic_protocol.python_parser import commands
from soniccontrol.procedures.procedure_controller import ProcedureController
from soniccontrol.updater import Updater
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import TabView
from soniccontrol.scripting.legacy_scripting import LegacyScriptingFacade
from soniccontrol.scripting.scripting_facade import ScriptingFacade
from soniccontrol.sonic_device import SonicDevice
from soniccontrol_gui.utils.animator import Animator, DotAnimationSequence
from soniccontrol_gui.constants import sizes, ui_labels
from soniccontrol.events import PropertyChangeEvent
from soniccontrol_gui.views.configuration.transducer_configs import ATConfig, ATConfigFrame, TransducerConfig, TransducerConfigSchema
from soniccontrol_gui.views.core.app_state import ExecutionState
from soniccontrol_gui.resources import images
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.widgets.file_browse_button import FileBrowseButtonView
from soniccontrol_gui.constants import files
from async_tkinter_loop import async_handler

from soniccontrol_gui.widgets.message_box import MessageBox
    

class Settings(UIComponent):
    def __init__(self, parent: UIComponent, device: SonicDevice, updater: Updater):
        self._logger = logging.getLogger(parent.logger.name + "." + Settings.__name__)
        
        self._logger.debug("Create Settings Component")
        self._view = SettingsView(parent.view, self)
        self._device = device
        self._updater = updater
        super().__init__(parent, self._view, self._logger)
        self._view.set_apply_settings_command(async_handler(self._apply_settings))

    async def _apply_settings(self) -> None:
        self._logger.debug("Apply settings")
        await self._updater.stop()
        self._logger.debug("Stopped updater")
        self._updater.set_update_interval(self._view.get_updater_interval())
        self._logger.debug("Set updater interval to %i", self._view.get_updater_interval())
        self._updater.start()
        self._logger.debug("Started updater")




class SettingsView(TabView):
    def __init__(self, master: ttk.Frame, presenter: UIComponent, *args, **kwargs):
        self._presenter = presenter
        super().__init__(master, *args, **kwargs)

    @property
    def image(self) -> ttk.ImageTk.PhotoImage:
        return ImageLoader.load_image_resource(images.SETTINGS_ICON_BLACK, sizes.TAB_ICON_SIZE)

    @property
    def tab_title(self) -> str:
        return ui_labels.SETTINGS_LABEL

    def _initialize_children(self) -> None:
        tab_name = "configuration"

        self._settings_frame: ttk.Frame = ttk.Frame(self)
        self._apply_settings_button: ttk.Button = ttk.Button(
            self._settings_frame,
            text=ui_labels.APPLY_SETTINGS,
            style=ttk.DARK,
            # image=utils.ImageLoader.load_image(
            #     images.PLUS_ICON_WHITE, sizes.BUTTON_ICON_SIZE
            # ),
        )
        self._updater_interval_label: ttk.Label = ttk.Label(
            self._settings_frame,
            text=ui_labels.UPDATER_INTERVAL_LABEL,
            style=ttk.DARK,
        )
        self._updater_interval: ttk.IntVar = ttk.IntVar()
        self._updater_interval_entry: ttk.Entry = ttk.Entry(
            self._settings_frame, textvariable=self._updater_interval, style=ttk.DARK
        )
        WidgetRegistry.register_widget(self._apply_settings_button, "apply_settings_button", tab_name)
        WidgetRegistry.register_widget(self._updater_interval_entry, "updater_interval_entry", tab_name)
        WidgetRegistry.register_widget(self._updater_interval_label, "updater_interval_label", tab_name)

    def _initialize_publish(self) -> None:
        self._settings_frame.pack(expand=True, fill=ttk.BOTH)
        self._settings_frame.columnconfigure(0, weight=sizes.DONT_EXPAND)
        self._settings_frame.columnconfigure(1, weight=sizes.EXPAND)
        self._settings_frame.columnconfigure(2, weight=sizes.DONT_EXPAND)
        self._settings_frame.columnconfigure(3, weight=sizes.DONT_EXPAND)
        self._settings_frame.columnconfigure(4, weight=sizes.DONT_EXPAND)
        self._settings_frame.rowconfigure(0, weight=sizes.DONT_EXPAND)
        self._settings_frame.rowconfigure(1, weight=sizes.EXPAND)
        self._apply_settings_button.grid(
            row=0,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )
        self._updater_interval_label.grid(
            row=0,
            column=1,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.EW,
        )
        self._updater_interval_entry.grid(
            row=0,
            column=2,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.EW,
        )

    def set_apply_settings_command(self, command: Callable[[], None]) -> None:
        self._apply_settings_button.configure(command=command)

    def get_updater_interval(self) -> int:
        return self._updater_interval.get()
