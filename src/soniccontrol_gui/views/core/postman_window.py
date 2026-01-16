import logging
from typing import Any, Dict
import ttkbootstrap as ttk
from sonic_protocol.field_names import EFieldName
from sonic_protocol.schema import IEFieldName
from soniccontrol.events import Event
from soniccontrol.sonic_device import SonicDevice
from soniccontrol.updater import Updater
from soniccontrol_gui.constants import style, ui_labels
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.view import View
from soniccontrol_gui.views.control.logging import Logging
from soniccontrol_gui.views.core.device_window import DeviceWindow, DeviceWindowView
from soniccontrol_gui.widgets.message_box import MessageBox


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


class PostmanStatusBarView(View):
    def __init__(
        self,
        master: ttk.Frame,
        *args,
        **kwargs
    ) -> None:
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


class WorkerConnectionTab(UIComponent):
    pass

class WorkerConnectionTabView(UIComponent):
    pass


class PostmanDeviceWindow(DeviceWindow):
    def __init__(self, device: SonicDevice, root, connection_name: str):
        self._logger: logging.Logger = logging.getLogger(connection_name + ".ui")
        self._device = device
        try:            
            self._view = DeviceWindowView(root=root, title=f"Device Window (Postman) - {connection_name}")
            super().__init__(self._logger, self._view, self._device.communicator)

            self._updater = Updater(self._device)
            self._logging = Logging(self, connection_name)

            self._status_bar = PostmanStatusBar(self, self._view.status_bar_slot) # type: ignore
            self._view.add_tab_views([
                self._logging.view, 
            ], right_one=False)

            self._updater.subscribe(Updater.UPDATE_EVENT,self._status_bar.on_update)
            self._updater.start()

        except Exception as e:
            self._logger.error(e)
            MessageBox.show_error(root, str(e))
            raise
