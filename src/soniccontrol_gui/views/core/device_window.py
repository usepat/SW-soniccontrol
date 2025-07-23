from typing import Callable, List, Optional, cast
import logging
from async_tkinter_loop import async_handler
import ttkbootstrap as ttk
import tkinter as tk

from sonic_protocol.command_codes import CommandCode
from soniccontrol.data_capturing.capture import Capture
from soniccontrol.data_capturing.capture_target import CaptureFree, CaptureProcedure, CaptureScript, CaptureSpectrumMeasure, CaptureTargets
from soniccontrol.scripting.new_scripting import NewScriptingFacade
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.view import TabView, View
from soniccontrol.communication.communicator import Communicator
from soniccontrol.procedures.procedure_controller import ProcedureController
from soniccontrol.scripting.interpreter_engine import InterpreterEngine
from soniccontrol.sonic_device import SonicDevice
from soniccontrol_gui.views.configuration.settings import Settings
from soniccontrol_gui.views.control.log_storage import LogStorage, NotDeviceLogFilter
from soniccontrol.updater import Updater
from soniccontrol_gui.constants import sizes, ui_labels
from soniccontrol.events import Event, EventManager
from soniccontrol_gui.views.configuration.configuration import Configuration
from soniccontrol_gui.views.configuration.legacy_configuration import LegacyConfiguration
from soniccontrol_gui.views.configuration.flashing import Flashing
from soniccontrol_gui.views.core.app_state import AppExecutionContext, AppState, ExecutionState
from soniccontrol_gui.views.home import Home
from soniccontrol_gui.views.info import Info
from soniccontrol_gui.views.control.logging import Logging, LoggingTab
from soniccontrol_gui.views.control.editor import Editor, ScriptFile
from soniccontrol_gui.views.control.proc_controlling import ProcControlling, ProcControllingModel
from soniccontrol_gui.views.control.serialmonitor import SerialMonitor
from soniccontrol_gui.views.measure.measuring import Measuring
from soniccontrol_gui.views.core.status import StatusBar
from soniccontrol_gui.views.measure.spectrum_measure import SpectrumMeasureTab, SpectrumMeasureModel
from soniccontrol_gui.widgets.message_box import DialogOptions, MessageBox
from soniccontrol_gui.widgets.notebook import Notebook
from soniccontrol_gui.resources import images
from soniccontrol_gui.constants import files


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
    
        self._app_state.app_execution_context = AppExecutionContext(ExecutionState.IDLE, None)

        self._communicator.subscribe(Communicator.DISCONNECTED_EVENT, lambda _e: self.on_disconnect())
        # This needs to be here, for the edge case, that the communicator got disconnected, before it could be subscribed
        if not self._communicator.connection_opened.is_set():
            self.on_disconnect()

    @async_handler
    async def on_disconnect(self) -> None:
        if not self._view.is_open:
            return # Window was closed already
        
        self._app_state.app_execution_context = AppExecutionContext(ExecutionState.NOT_RESPONSIVE, None)
        
        # Window is open, Ask User if he wants to close it
        message_box = MessageBox.show_ok_cancel(self._view.root, ui_labels.DEVICE_DISCONNECTED_MSG, ui_labels.DEVICE_DISCONNECTED_TITLE)
        answer: Optional[DialogOptions] = await message_box.wait_for_answer()
        if answer is None or answer == DialogOptions.CANCEL:
            return
        else:
            self.close()

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

            self._logger.debug("Create logStorage for storing logs")
            self._logStorage = LogStorage()
            log_storage_handler = self._logStorage.create_log_handler()
            logging.getLogger(connection_name).addHandler(log_storage_handler)
            not_device_log_filter = NotDeviceLogFilter()
            log_storage_handler.addFilter(not_device_log_filter)
            log_storage_handler.setLevel(logging.DEBUG)

             # Models
            self._proc_controller = ProcedureController(self._device, EventManager()) # FIXME: what to do if devices do not support updates?
            self._scripting = NewScriptingFacade()
            self._script_file = ScriptFile(logger=self._logger)
            self._interpreter = InterpreterEngine(self._device, EventManager(), self._logger) # type: ignore
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
    def __init__(self, device: SonicDevice, root, connection_name: str, is_legacy_device: bool = False):
        self._logger: logging.Logger = logging.getLogger(connection_name + ".ui")
        try:
            self._device = device
            
            self._view = DeviceWindowView(root, title=f"Device Window - {connection_name}")
            super().__init__(self._logger, self._view, self._device.communicator)

            # Models
            self._updater = Updater(self._device, time_waiting_between_updates_ms=(1000 * is_legacy_device))
            self._proc_controller = ProcedureController(self._device, self._updater)
            self._proc_controlling_model = ProcControllingModel()
            self._scripting = NewScriptingFacade()
            self._script_file = ScriptFile(logger=self._logger)
            self._interpreter = InterpreterEngine(self._device, self._updater, self._logger)
            self._spectrum_measure_model = SpectrumMeasureModel()

            self._capture = Capture(files.MEASUREMENTS_DIR, self._logger)
            self._capture_targets = {
                CaptureTargets.FREE: CaptureFree(),
                CaptureTargets.SCRIPT: CaptureScript(self._script_file, self._scripting, self._interpreter),
                CaptureTargets.PROCEDURE: CaptureProcedure(self._proc_controller, self._proc_controlling_model),
                CaptureTargets.SPECTRUM_MEASURE: CaptureSpectrumMeasure(self._updater, self._proc_controller, self._spectrum_measure_model)
            }

            update_answer_fields = self._device.protocol.command_contracts[CommandCode.GET_UPDATE].answer_def.fields

            # Components
            self._logger.debug("Create views")
            self._serialmonitor = SerialMonitor(self, self._device.communicator)
            self._spectrum_measure = SpectrumMeasureTab(self, self._spectrum_measure_model)
            self._logging = Logging(self, connection_name)
            self._editor = Editor(self, self._scripting, self._script_file, self._interpreter, self._app_state)
            self._status_bar = StatusBar(self, self._view.status_bar_slot, update_answer_fields)
            self._info = Info(self)
            if is_legacy_device:
                self._configuration = LegacyConfiguration(self, self._device, self._proc_controller)
            else:
                self._configuration = Configuration(self, self._device, self._updater)
            self._settings = Settings(self, self._device, self._updater)
            
            self._proc_controlling = ProcControlling(self, self._proc_controller, self._proc_controlling_model, self._app_state)
            self._sonicmeasure = Measuring(self, self._capture , self._capture_targets, self._device.info)
            self._home = Home(self, self._device)
            flashing_view = None
            
            if is_legacy_device:
                self._flashing = Flashing(self, self._logger, self._app_state, self._updater, connection_name, self._device)
                self._flashing.subscribe(Flashing.RECONNECT_EVENT, lambda _e: self.reconnect_after_flashing(True))
                self._flashing.subscribe(Flashing.FAILED_EVENT, lambda _e: self.reconnect_after_flashing(False))
                flashing_view = self._flashing.view


            # Views
            self._logger.debug("Created all views, add them as tabs")
            self._view.add_tab_views([
                self._home.view,
                self._serialmonitor.view,
                self._spectrum_measure.view, 
                self._proc_controlling.view,
                self._editor.view, 
                self._configuration.view, 
                self._settings.view,
                flashing_view
            ], right_one=False)
            self._view.add_tab_views([
                self._info.view,
                self._sonicmeasure.view, 
                self._logging.view, 
            ], right_one=True)

            
            self._logger.debug("add callbacks and listeners to event emitters")
            self._updater.subscribe("update", lambda e: self._capture.on_update(e.data["status"]))
            self._updater.subscribe("update", lambda e: self._status_bar.on_update_status(e.data["status"]))
            self._updater.start()
            self._app_state.subscribe_property_listener(AppState.EXECUTION_STATE_PROP_NAME, self._serialmonitor.on_execution_state_changed)
            self._app_state.subscribe_property_listener(AppState.EXECUTION_STATE_PROP_NAME, self._configuration.on_execution_state_changed)
            self._app_state.subscribe_property_listener(AppState.EXECUTION_STATE_PROP_NAME, self._home.on_execution_state_changed)
        except Exception as e:
            self._logger.error(e)
            MessageBox.show_error(root, str(e))
            raise

    @async_handler
    async def reconnect_after_flashing(self, success: bool):
        if success:
            message = ui_labels.DEVICE_FLASHED_SUCCESS_MSG
        else:
            message = ui_labels.DEVICE_FLASHED_FAILED_MSG
        message_box = MessageBox.show_ok(self.view.root, message, ui_labels.DEVICE_FLASHED_TITLE)
        await message_box.wait_for_answer()
        self.reconnect()


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
        self._notebook_right: Notebook = Notebook(self._paned_window, "right")
        self._notebook_left: Notebook = Notebook(self._paned_window, "left")
        self._status_bar_slot: ttk.Frame = ttk.Frame(self._frame)

        self._frame.pack(fill=ttk.BOTH, expand=True)
        self._paned_window.pack(fill=ttk.BOTH, expand=True)
        self._status_bar_slot.pack(side=ttk.BOTTOM, fill=ttk.X)
        self._notebook_left.pack(side=ttk.LEFT, fill=ttk.BOTH)
        self._notebook_right.pack(side=ttk.LEFT, fill=ttk.BOTH)

        self._paned_window.add(self._notebook_left, minsize=600)
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

    def add_tab_views(self, tab_views: List[TabView | None], right_one: bool = False):
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
