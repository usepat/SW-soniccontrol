from typing import Callable, List, Optional, cast
import logging
from async_tkinter_loop import async_handler
import ttkbootstrap as ttk
import tkinter as tk

from ttkbootstrap.dialogs.dialogs import Messagebox

from sonic_protocol.command_codes import CommandCode
from soniccontrol_gui.state_fetching.capture import Capture
from soniccontrol_gui.state_fetching.capture_target import CaptureFree, CaptureProcedure, CaptureScript, CaptureSpectrumMeasure, CaptureTargets
from soniccontrol_gui.state_fetching.spectrum_measure import SpectrumMeasureModel
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import TabView, View
from soniccontrol.communication.communicator import Communicator
from soniccontrol.procedures.procedure_controller import ProcedureController
from soniccontrol.scripting.interpreter_engine import InterpreterEngine
from soniccontrol.scripting.legacy_scripting import LegacyScriptingFacade
from soniccontrol.scripting.scripting_facade import BuiltInFunctions
from soniccontrol.sonic_device import SonicDevice
from soniccontrol_gui.state_fetching.logger import LogStorage, NotDeviceLogFilter
from soniccontrol_gui.state_fetching.updater import Updater
from soniccontrol_gui.constants import sizes, ui_labels
from soniccontrol.events import Event, EventManager
from soniccontrol_gui.views.configuration.configuration import Configuration
from soniccontrol_gui.views.configuration.flashing import Flashing
from soniccontrol_gui.views.core.app_state import AppState, ExecutionState
from soniccontrol_gui.views.home import Home
from soniccontrol_gui.views.info import Info
from soniccontrol_gui.views.control.logging import Logging, LoggingTab
from soniccontrol_gui.views.control.editor import Editor, ScriptFile
from soniccontrol_gui.views.control.proc_controlling import ProcControlling, ProcControllingModel
from soniccontrol_gui.views.control.serialmonitor import SerialMonitor
from soniccontrol_gui.views.measure.measuring import Measuring
from soniccontrol_gui.views.core.status import StatusBar
from soniccontrol_gui.widgets.notebook import Notebook
from soniccontrol_gui.resources import images


class DeviceWindow(UIComponent):
    CLOSE_EVENT = "Close"
    RECONNECT_EVENT = "Reconnect"

    def __init__(self, logger: logging.Logger, deviceWindowView: "DeviceWindowView", communicator: Communicator):
        self._logger = logger
        self._communicator = communicator
        self._view = deviceWindowView
        super().__init__(None, self._view, self._logger)
        self._app_state = AppState(self._logger)

        self._view.add_close_callback(self.close)
        self._communicator.subscribe(Communicator.DISCONNECTED_EVENT, lambda _e: self.on_disconnect())
    
        self._app_state.execution_state = ExecutionState.IDLE

    def on_disconnect(self) -> None:
        if not self._view.is_open:
            return # Window was closed already
        
        self._app_state.execution_state = ExecutionState.NOT_RESPONSIVE
        
        # Window is open, Ask User if he wants to close it
        answer: Optional[str] = cast(Optional[str], Messagebox.okcancel(ui_labels.DEVICE_DISCONNECTED_MSG, ui_labels.DEVICE_DISCONNECTED_TITLE))
        if answer is None or answer == "Cancel":
            return
        else:
            self.close()

    def on_reconnect(self, success : bool) -> None:
        if success:
            message = ui_labels.DEVICE_FLASHED_SUCCESS_MSG
        else:
            message = ui_labels.DEVICE_FLASHED_FAILED_MSG
        Messagebox.ok(message, ui_labels.DEVICE_FLASHED_TITLE)
        self.reconnect()

    @async_handler
    async def close(self) -> None:
        self._logger.info("Close window")
        self.emit(Event(DeviceWindow.CLOSE_EVENT))
        self._view.close()
        await self._communicator.close_communication()

    @async_handler
    async def reconnect(self) -> None:
        self._logger.info("Close window")
        await self._communicator.close_communication(True)
        self.emit(Event(DeviceWindow.RECONNECT_EVENT))
        self._view.close()
        

class RescueWindow(DeviceWindow):
    def __init__(self, device: SonicDevice, root, connection_name: str):
        self._logger: logging.Logger = logging.getLogger(connection_name + ".ui")
        try:
            self._device = device
            self._view = DeviceWindowView(root, title=f"Rescue Window - {connection_name}")
            super().__init__(self._logger, self._view, self._device.communicator)

            self._flashing = Flashing(self, self._logger, self._device, self._app_state)
            self._flashing.subscribe(Flashing.RECONNECT_EVENT, lambda _e: self.on_reconnect(True))
            self._flashing.subscribe(Flashing.FAILED_EVENT, lambda _e: self.on_reconnect(False))


            self
            self._logger.debug("Create logStorage for storing logs")
            self._logStorage = LogStorage()
            log_storage_handler = self._logStorage.create_log_handler()
            logging.getLogger(connection_name).addHandler(log_storage_handler)
            not_device_log_filter = NotDeviceLogFilter()
            log_storage_handler.addFilter(not_device_log_filter)
            log_storage_handler.setLevel(logging.DEBUG)

             # Models
            self._proc_controller = ProcedureController(self._device, EventManager()) # FIXME: what to do if devices do not support updates?
            self._scripting = LegacyScriptingFacade(
                self._device, 
                self._proc_controller,
                include_command_aliases=[BuiltInFunctions.ON, BuiltInFunctions.OFF, BuiltInFunctions.HOLD]
            )
            self._script_file = ScriptFile(logger=self._logger)
            self._interpreter = InterpreterEngine(self._logger)
            self._app_state = AppState(self._logger)

            self._logger.debug("Create views")
            self._serialmonitor = SerialMonitor(self, self._device.communicator)
            self._scripting = Editor(self, self._scripting, self._script_file, self._interpreter, self._app_state)
            self._logging = LoggingTab(self, self._logStorage.logs)
            self._home = Home(self, self._device)

            self._logger.debug("Created all views, add them as tabs")
            self._view.add_tab_views([
                self._home.view,
                self._scripting.view,
                self._serialmonitor.view, 
                self._flashing.view,
            ], right_one=False)
            self._view.add_tab_views([
                self._logging.view, 
            ], right_one=True)

            self._logger.debug("add callbacks and listeners to event emitters")

            self._app_state.subscribe_property_listener(AppState.EXECUTION_STATE_PROP_NAME, self._serialmonitor.on_execution_state_changed)
            self._app_state.subscribe_property_listener(AppState.EXECUTION_STATE_PROP_NAME, self._home.on_execution_state_changed)
        
        except Exception as e:
            self._logger.error(e)
            raise


class KnownDeviceWindow(DeviceWindow):
    def __init__(self, device: SonicDevice, root, connection_name: str):
        self._logger: logging.Logger = logging.getLogger(connection_name + ".ui")
        try:
            self._device = device
            self._view = DeviceWindowView(root, title=f"Device Window - {connection_name}")
            super().__init__(self._logger, self._view, self._device.communicator)

            # Models
            self._updater = Updater(self._device)
            self._proc_controller = ProcedureController(self._device, self._updater)
            self._proc_controlling_model = ProcControllingModel()
            self._scripting = LegacyScriptingFacade(self._device, self._proc_controller)
            self._script_file = ScriptFile(logger=self._logger)
            self._interpreter = InterpreterEngine(self._logger)
            self._spectrum_measure_model = SpectrumMeasureModel()

            update_answer_fields = self._device.lookup_table[CommandCode.DASH].answer_def.fields
            update_answer_field_names = [ field.field_name for field in update_answer_fields ] 
            self._capture = Capture(update_answer_field_names, self._logger)
            self._capture_targets = {
                CaptureTargets.FREE: CaptureFree(),
                CaptureTargets.SCRIPT: CaptureScript(self._script_file, self._scripting, self._interpreter),
                CaptureTargets.PROCEDURE: CaptureProcedure(self._proc_controller, self._proc_controlling_model),
                CaptureTargets.SPECTRUM_MEASURE: CaptureSpectrumMeasure(self._updater, self._proc_controller, self._spectrum_measure_model)
            }

            # Components
            self._logger.debug("Create views")
            self._serialmonitor = SerialMonitor(self, self._device.communicator)
            self._logging = Logging(self, connection_name)
            self._editor = Editor(self, self._scripting, self._script_file, self._interpreter, self._app_state)
            self._status_bar = StatusBar(self, self._view.status_bar_slot, update_answer_fields)
            self._info = Info(self)
            self._configuration = Configuration(self, self._device, self._proc_controller)
            self._flashing = Flashing(self, self._logger, self._device, self._app_state, self._updater)
            self._flashing.subscribe(Flashing.RECONNECT_EVENT, lambda _e: self.on_reconnect(True))
            self._flashing.subscribe(Flashing.FAILED_EVENT, lambda _e: self.on_reconnect(False))
            self._proc_controlling = ProcControlling(self, self._proc_controller, self._proc_controlling_model, self._app_state)
            self._sonicmeasure = Measuring(self, self._capture , self._capture_targets, self._spectrum_measure_model)
            self._home = Home(self, self._device)

            # Views
            self._logger.debug("Created all views, add them as tabs")
            self._view.add_tab_views([
                self._home.view,
                self._serialmonitor.view, 
                self._proc_controlling.view,
                self._editor.view, 
                self._configuration.view, 
                self._flashing.view,
            ], right_one=False)
            self._view.add_tab_views([
                self._info.view,
                self._sonicmeasure.view, 
                self._logging.view, 
            ], right_one=True)

            self._logger.debug(list(WidgetRegistry._widget_registry.keys()))

            self._logger.debug("add callbacks and listeners to event emitters")
            self._updater.subscribe("update", lambda e: self._capture.on_update(e.data["status"]))
            self._updater.subscribe("update", lambda e: self._status_bar.on_update_status(e.data["status"]))
            self._updater.start()
            self._app_state.subscribe_property_listener(AppState.EXECUTION_STATE_PROP_NAME, self._serialmonitor.on_execution_state_changed)
            self._app_state.subscribe_property_listener(AppState.EXECUTION_STATE_PROP_NAME, self._configuration.on_execution_state_changed)
            self._app_state.subscribe_property_listener(AppState.EXECUTION_STATE_PROP_NAME, self._home.on_execution_state_changed)
        except Exception as e:
            self._logger.error(e)
            raise


class DeviceWindowView(tk.Toplevel, View):
    def __init__(self, root, *args, **kwargs) -> None:
        title = kwargs.pop("title", "Device Window")
        super().__init__(root, *args, **kwargs)
        self.title(title)
        self.geometry('1200x800')
        self.minsize(600, 400)
        self.iconphoto(True, ImageLoader.load_image_resource(images.LOGO, sizes.LARGE_BUTTON_ICON_SIZE))

        self.wm_title(ui_labels.IDLE_TITLE)
        ttk.Style(ui_labels.THEME)
        self.option_add("*Font", "OpenSans 10")
        self._default_font = ttk.font.nametofont("TkDefaultFont")
        self._default_font.configure(family="OpenSans", size=10)

        # tkinter components
        self._frame: ttk.Frame = ttk.Frame(self)
        # We use the tk.PanedWindow, because ttk.PanedWindow do not support minsize and paneconfigure
        self._paned_window: tk.PanedWindow = tk.PanedWindow(self._frame, orient=ttk.HORIZONTAL)
        self._notebook_right: Notebook = Notebook(self._paned_window)
        self._notebook_left: Notebook = Notebook(self._paned_window)
        self._status_bar_slot: ttk.Frame = ttk.Frame(self._frame)

        self._frame.pack(fill=ttk.BOTH, expand=True)
        self._paned_window.pack(fill=ttk.BOTH, expand=True)
        self._status_bar_slot.pack(side=ttk.BOTTOM, fill=ttk.X)
        self._notebook_left.pack(side=ttk.LEFT, fill=ttk.BOTH)
        self._notebook_right.pack(side=ttk.LEFT, fill=ttk.BOTH)

        self._paned_window.add(self._notebook_left, minsize=300)
        self._paned_window.add(self._notebook_right, minsize=300)

        self._notebook_right.add_tabs(
            [],
            show_titles=True,
            show_images=True,
        )
        self._notebook_left.add_tabs(
            [],
            show_titles=True,
            show_images=True,
        )


    @property
    def status_bar_slot(self) -> ttk.Frame:
        return self._status_bar_slot
    
    @property
    def is_open(self) -> bool:
        return self.winfo_exists()

    def add_tab_views(self, tab_views: List[TabView], right_one: bool = False):
        notebook = self._notebook_right if right_one else self._notebook_left
        notebook.add_tabs(
            tab_views,
            show_titles=True,
            show_images=True,
        )

    def add_close_callback(self, callback: Callable[[], None]) -> None:
        self.protocol("WM_DELETE_WINDOW", callback)

    def close(self) -> None:
        self.destroy()
