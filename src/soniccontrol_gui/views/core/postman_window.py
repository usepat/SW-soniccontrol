import logging
from typing import Any, Callable, Dict
import ttkbootstrap as ttk
from async_tkinter_loop import async_handler
from sonic_protocol.field_names import EFieldName
from sonic_protocol.schema import IEFieldName
from soniccontrol.builder import DeviceBuilder
from soniccontrol.communication.communicator import Communicator
from soniccontrol.events import Event, PropertyChangeEvent
from soniccontrol.sonic_device import SonicDevice
from soniccontrol.updater import Updater
from soniccontrol_gui.constants import style, ui_labels, sizes
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.view import TabView, View
from soniccontrol_gui.views.control.logging import Logging
from soniccontrol_gui.views.control.serialmonitor import SerialMonitor
from soniccontrol_gui.views.core.app_state import AppState, ExecutionState
from soniccontrol_gui.views.core.device_window import DeviceWindow, DeviceWindowView, KnownDeviceWindow
from soniccontrol_gui.widgets.message_box import MessageBox
from soniccontrol_gui.resources import images


class PostmanStatusBar(UIComponent):
    def __init__(self, parent: UIComponent, parent_slot: View):
        self._logger = logging.getLogger(parent.logger.name + "." + PostmanStatusBar.__name__)

        self._view = PostmanStatusBarView(parent_slot)
        super().__init__(parent, self._view, self._logger)

    def on_update(self, e: Event):
        connection_status: Dict[IEFieldName, Any] = e.data["status"]
        is_connected = connection_status[EFieldName.IS_CONNECTED]
        self._view.set_is_connected_label_text(ui_labels.CONNECTED_LABEL if is_connected else ui_labels.NOT_CONNECTED)
        self._view.set_is_connected_label_color(style.INVERSE_SECONDARY if is_connected else style.INVERSE_DANGER)


class WorkerConnectionTab(UIComponent):
    def __init__(self, parent: UIComponent, device: SonicDevice, connection_name: str):
        self._logger = logging.getLogger(parent.logger.name + "." + WorkerConnectionTab.__name__)

        self._view = WorkerConnectionTabView(parent.view)
        super().__init__(parent, self._view, self._logger)

        self._device = device
        self._connection_name = connection_name
        self._worker_device_window: DeviceWindow | None = None

        self._view.set_connection_button_pressed_callback(self._on_connect)

    @async_handler
    async def _on_connect(self):
        self._view.enable_connection_button(False)

        assert self._worker_device_window is None, "there exists already a device window for the worker"

        try:
            builder = DeviceBuilder(logger=self._logger)
            worker_device = await builder.build_amp(self._device.communicator)
        except Exception as e:
            self._logger.error(e)
            message = ui_labels.COULD_NOT_CONNECT_MESSAGE.format(str(e))
            MessageBox.show_error(self._view.root, message)

            self._view.enable_connection_button(True)
        else:
            self._worker_device_window = KnownDeviceWindow(worker_device, self._view.root, self._connection_name)
            self._worker_device_window.view.focus_set()
            worker_device.communicator.subscribe(Communicator.DISCONNECTED_EVENT, self._on_close_communication)
            self._worker_device_window.subscribe(DeviceWindow.CLOSE_EVENT, self._on_close_communication)  
            self._worker_device_window.subscribe(DeviceWindow.RECONNECT_EVENT, lambda _: self._on_connect())
        

    @async_handler
    async def _on_close_communication(self, e: Event):
        self._worker_device_window = None
        self._view.enable_connection_button(True)

    def on_execution_state_changed(self, e: PropertyChangeEvent):
        execution_state: ExecutionState = e.new_value.execution_state
        if execution_state == ExecutionState.NOT_RESPONSIVE:
            self._view.enable_connection_button(False)
            if self._worker_device_window:
                self._worker_device_window.close()


class PostmanDeviceWindow(DeviceWindow):
    def __init__(self, device: SonicDevice, root, connection_name: str):
        self._logger: logging.Logger = logging.getLogger(connection_name + ".ui")
        self._device = device
        try:            
            self._view = DeviceWindowView(root=root, title=f"Device Window - Postman - {connection_name}")
            super().__init__(self._logger, self._view, self._device.communicator)

            self._updater = Updater(self._device)
            self._serialmonitor = SerialMonitor(self, self._device.communicator)
            self._logging = Logging(self, connection_name)
            self._worker_connection = WorkerConnectionTab(self, self._device, connection_name)

            # TODO: add modbus config view

            self._status_bar = PostmanStatusBar(self, self._view.status_bar_slot) # type: ignore
            self._view.add_tab_views([
                self._worker_connection.view,
                self._serialmonitor.view,
            ], right_one=False)
            self._view.add_tab_views([
                self._logging.view
            ], right_one=True)

            self._updater.subscribe(Updater.UPDATE_EVENT,self._status_bar.on_update)
            self._updater.start()
            self.app_state.subscribe_property_listener(AppState.APP_EXECUTION_CONTEXT_PROP_NAME, self._worker_connection.on_execution_state_changed)


        except Exception as e:
            self._logger.error(e)
            MessageBox.show_error(root, str(e))
            raise


class PostmanStatusBarView(View):
    def __init__(self, master: ttk.Frame, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        self._status_bar_frame: ttk.Frame = ttk.Frame(self)

        self._connection_label_text = ttk.StringVar(self, ui_labels.NOT_CONNECTED)
        self._connection_label = ttk.Label(
            self._status_bar_frame,
            textvariable=self._connection_label_text,
            bootstyle=style.INVERSE_SECONDARY
        )

    def _initialize_publish(self) -> None:
        self.pack(fill=ttk.BOTH, padx=3, pady=3)
        self._status_bar_frame.pack(side=ttk.BOTTOM, fill=ttk.X)
        self._connection_label.pack(side=ttk.LEFT, padx=5)

    def set_is_connected_label_text(self, text: str):
        self._connection_label_text.set(text)

    def set_is_connected_label_color(self, color: str):
        self._connection_label.configure(color)


class WorkerConnectionTabView(TabView):
    def __init__(self, master: ttk.Frame, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    #TODO: better icon and label needed
    @property
    def image(self) -> ttk.ImageTk.PhotoImage:
        return ImageLoader.load_image_resource(images.HOME_ICON_BLACK, sizes.TAB_ICON_SIZE)

    @property
    def tab_title(self) -> str:
        return ui_labels.HOME_LABEL

    def _initialize_children(self) -> None:
        self._connection_button = ttk.Button(
            self, 
            text=ui_labels.CONNECT_LABEL,
            bootstyle=ttk.DARK
        )

    def _initialize_publish(self) -> None:
        self.pack(fill=ttk.BOTH, padx=3, pady=3)
        self._connection_button.pack(side=ttk.LEFT, padx=sizes.MEDIUM_PADDING, pady=sizes.MEDIUM_PADDING)

    def set_connection_button_pressed_callback(self, callback: Callable[[], None]):
        self._connection_button.configure(command=callback)

    def enable_connection_button(self, enabled: bool):
        self._connection_button.configure(state=ttk.NORMAL if enabled else ttk.DISABLED)
