import logging
from typing import Any, Callable, Dict
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
from async_tkinter_loop import async_handler
from sonic_protocol.field_names import EFieldName
from sonic_protocol.schema import IEFieldName
from soniccontrol.builder import DeviceBuilder
from soniccontrol.communication.communicator import Communicator
from soniccontrol.communication.postman_proxy_communicator import PostmanProxyCommunicator
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
from soniccontrol_gui.views.home import DeviceInfoFrame
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
        self._view.set_is_connected_label_text(
            ui_labels.CONNECTED_TO_WORKER if is_connected else ui_labels.NOT_CONNECTED_TO_WORKER)
        self._view.set_is_connected_label_color(
            style.INVERSE_SECONDARY if is_connected else style.INVERSE_DANGER)


class PostmanHomeTab(UIComponent):
    def __init__(self, parent: UIComponent, device: SonicDevice, connection_name: str):
        self._logger = logging.getLogger(parent.logger.name + "." + PostmanHomeTab.__name__)
        self._device = device
        self._connection_name = connection_name
        self._worker_device_window: DeviceWindow | None = None

        self._view = PostmanHomeTabView(parent.view)
        super().__init__(parent, self._view, self._logger)

        self._info_frame = DeviceInfoFrame(self, self._view.info_frame_slot, "postman_home", self._device)

        self._view.set_connect_to_worker_button_pressed_callback(self._on_connect_to_worker)
        self._view.enable_connection_button(False)

    @async_handler
    async def _on_connect_to_worker(self):
        self._view.enable_connection_button(False)

        assert self._worker_device_window is None, "there exists already a device window for the worker"

        try:
            builder = DeviceBuilder(logger=self._logger)
            proxy_comm = PostmanProxyCommunicator(self._device.communicator)
            worker_device = await builder.build_amp(proxy_comm)
        except Exception as e:
            self._logger.error(e)
            message = ui_labels.COULD_NOT_CONNECT_MESSAGE.format(str(e))
            MessageBox.show_error(self._view.root, message)

            self._view.enable_connection_button(True)
        else:
            self._worker_device_window = KnownDeviceWindow(
                worker_device, self._view.root, self._connection_name)
            self._worker_device_window.view.focus_set()
            worker_device.communicator.subscribe(Communicator.DISCONNECTED_EVENT, self._on_close_communication_worker)
            self._worker_device_window.subscribe(DeviceWindow.CLOSE_EVENT, self._on_close_communication_worker)  
            self._worker_device_window.subscribe(DeviceWindow.RECONNECT_EVENT, lambda _: self._on_connect_to_worker())
        

    @async_handler
    async def _on_close_communication_worker(self, e: Event):
        self._worker_device_window = None
        self._view.enable_connection_button(True)

    def on_execution_state_changed(self, e: PropertyChangeEvent):
        self._info_frame.on_execution_state_changed(e)

        execution_state: ExecutionState = e.new_value.execution_state
        if execution_state == ExecutionState.NOT_RESPONSIVE:
            self._view.enable_connection_button(False)
            if self._worker_device_window:
                self._worker_device_window.close()

    def on_update(self, e: Event):
        connection_status: Dict[IEFieldName, Any] = e.data["status"]
        is_connected = connection_status[EFieldName.IS_CONNECTED]
        self._view.enable_connection_button(is_connected)


class PostmanDeviceWindow(DeviceWindow):
    def __init__(self, device: SonicDevice, root, connection_name: str):
        self._logger: logging.Logger = logging.getLogger(connection_name + ".ui")
        self._device = device
        try:            
            self._view = DeviceWindowView(root=root, title=f"Device Window - Postman - {connection_name}")
            super().__init__(self._logger, self._view, self._device.communicator)

            self._updater = Updater(self._device)
            self._updater.set_update_interval(1000)
            self._serialmonitor = SerialMonitor(self, self._device.communicator)
            self._logging = Logging(self, connection_name)
            self._worker_connection_tab = PostmanHomeTab(self, self._device, connection_name)

            # TODO: add modbus config view

            self._status_bar = PostmanStatusBar(self, self._view.status_bar_slot) # type: ignore
            self._view.add_tab_views([
                self._worker_connection_tab.view,
                self._serialmonitor.view,
            ], right_one=False)
            self._view.add_tab_views([
                self._logging.view
            ], right_one=True)

            self._updater.subscribe(Updater.UPDATE_EVENT,self._status_bar.on_update)
            self._updater.subscribe(Updater.UPDATE_EVENT,self._worker_connection_tab.on_update)
            self._updater.start()
            self.app_state.subscribe_property_listener(AppState.APP_EXECUTION_CONTEXT_PROP_NAME, self._worker_connection_tab.on_execution_state_changed)

        except Exception as e:
            self._logger.error(e)
            MessageBox.show_error(root, str(e))
            raise


class PostmanStatusBarView(View):
    def __init__(self, master: ttk.Frame, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        self._status_bar_frame: ttk.Frame = ttk.Frame(self)

        self._connection_label_text = ttk.StringVar(self, ui_labels.NOT_CONNECTED_TO_WORKER)
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
        self._connection_label.configure(bootstyle=color)


class PostmanHomeTabView(TabView):
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

        self._main_frame: ScrolledFrame = ScrolledFrame(self, autohide=True)

        self._info_frame_slot = ttk.Frame(self._main_frame)
        # Control frame - contains the form and send button
        self._worker_frame: ttk.LabelFrame = ttk.LabelFrame(
            self._main_frame, text=ui_labels.WORKER_LABEL
        )

        self._connect_to_worker_button = ttk.Button(
            self._worker_frame, 
            text=ui_labels.OPEN_WORKER_WINDOW,
            bootstyle=ttk.DARK
        )

    def _initialize_publish(self) -> None:
        self.pack(fill=ttk.BOTH, padx=3, pady=3)
        self._main_frame.pack(fill=ttk.BOTH, expand=True)
        
        self._info_frame_slot.pack(fill=ttk.X)
        self._worker_frame.pack(fill=ttk.BOTH, expand=True, pady=(0, sizes.LARGE_PADDING), ipady=sizes.LARGE_PADDING)
        self._connect_to_worker_button.pack(side=ttk.LEFT, padx=sizes.MEDIUM_PADDING, pady=sizes.MEDIUM_PADDING)

    @property
    def info_frame_slot(self) -> View:
        return self._info_frame_slot #type: ignore

    def set_connect_to_worker_button_pressed_callback(self, callback: Callable[[], None]):
        self._connect_to_worker_button.configure(command=callback)

    def enable_connection_button(self, enabled: bool):
        self._connect_to_worker_button.configure(state=ttk.NORMAL if enabled else ttk.DISABLED)
