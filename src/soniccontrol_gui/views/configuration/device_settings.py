import asyncio
import attrs
import logging
from typing import Callable
import ttkbootstrap as ttk
from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocols.protocol_v3_0_0.protocol_v3_0_0 import Parity, UartInterface
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import TabView, View
from soniccontrol.sonic_device import SonicDevice
from soniccontrol_gui.constants import sizes, ui_labels
from soniccontrol_gui.resources import images
from soniccontrol_gui.utils.image_loader import ImageLoader
from async_tkinter_loop import async_handler
from soniccontrol import commands

from soniccontrol_gui.widgets.form_widget import FormWidget
from soniccontrol_gui.widgets.message_box import MessageBox


@attrs.define()
class ModbusSettings:
    parity: Parity = attrs.field(default=Parity.EVEN)
    baudrate: int = attrs.field(default=19200)
    interface: UartInterface = attrs.field(default=UartInterface.RS485)
    server_address: int = attrs.field(default=1)

@attrs.define()
class DeviceSettings:
    modbus_settings: ModbusSettings = attrs.field(factory=ModbusSettings)


class DeviceSettingsTab(UIComponent):
    def __init__(self, parent: UIComponent, device: SonicDevice):
        self._logger = logging.getLogger(parent.logger.name + "." + DeviceSettingsTab.__name__)
        self._device = device

        self._logger.debug("Create Device Settings Component")
        self._view = DeviceSettingsTabView(parent.view, parent_widget_name=parent.component_name)
        self._form = FormWidget(
            self, self._view.settings_form_slot, 
            "Device Settings", DeviceSettings, "device_settings_form"
        )

        super().__init__(parent, self._view, self._logger)
        self._view.set_apply_settings_command(self._apply_settings)
        self._view.set_load_settings_command(self._load_settings)

        self._load_settings()


    @async_handler
    async def _apply_settings(self) -> None:
        self._logger.debug("Apply settings")
        settings: DeviceSettings = self._form.attrs_object
        modbus_settings = settings.modbus_settings

        if not self._device.has_command(commands.GetModbusSettings()):
            return        
        
        self._view.set_apply_settings_button_enabled(False)
        try:
            await self._device.execute_command(commands.SetModbusBaudrate(modbus_settings.baudrate))
            await self._device.execute_command(commands.SetModbusInterface(modbus_settings.interface))
            await self._device.execute_command(commands.SetModbusParity(modbus_settings.parity))
            await self._device.execute_command(commands.SetModbusServerAddress(modbus_settings.server_address))
        except asyncio.CancelledError:
            raise
        except Exception as e:
            MessageBox.show_error(self._view.root, str(e))
        finally:
            self._view.set_apply_settings_button_enabled(True)


    @async_handler
    async def _load_settings(self) -> None:
        if not self._device.has_command(commands.GetModbusSettings()):
            return

        answer = await self._device.execute_command(commands.GetModbusSettings())

        self._form.attrs_object = DeviceSettings(
            modbus_settings=ModbusSettings(
                parity=answer[EFieldName.PARITY],
                baudrate=answer[EFieldName.BAUDRATE],
                interface=answer[EFieldName.UART_INTERFACE],
                server_address=answer[EFieldName.MODBUS_SERVER_ID],
            )
        )


class DeviceSettingsTabView(TabView):
    def __init__(self, master: ttk.Frame, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

    @property
    def image(self) -> ttk.ImageTk.PhotoImage:
        return ImageLoader.load_image_resource(images.SETTINGS_ICON_BLACK, sizes.TAB_ICON_SIZE)

    @property
    def tab_title(self) -> str:
        return ui_labels.SETTINGS_LABEL

    def _initialize_children(self) -> None:
        tab_name = "device_settings"
        if self._parent_widget_name:
            tab_name = self._parent_widget_name + "." + tab_name 

        self._settings_form_slot: ttk.Frame = ttk.Frame(self)
        self._control_frame: ttk.Frame = ttk.Frame(self)
        self._apply_settings_button: ttk.Button = ttk.Button(
            self._control_frame,
            text=ui_labels.APPLY_SETTINGS,
            style=ttk.DARK
        )
        self._load_settings_button: ttk.Button = ttk.Button(
            self._control_frame,
            text=ui_labels.LOAD_SETTINGS,
            style=ttk.DARK
        )
        WidgetRegistry.register_widget(self._apply_settings_button, "apply_settings_button", tab_name)
        WidgetRegistry.register_widget(self._load_settings_button, "load_settings_button", tab_name)

    def _initialize_publish(self) -> None:
        self._settings_form_slot.pack(side=ttk.TOP, fill=ttk.BOTH, expand=True)
        self._control_frame.pack(side=ttk.BOTTOM, fill=ttk.X, expand=True, pady=sizes.LARGE_PADDING)
        self._apply_settings_button.pack(side=ttk.LEFT, padx=sizes.SMALL_PADDING)
        self._load_settings_button.pack(side=ttk.LEFT, padx=sizes.SMALL_PADDING)
        
    def set_apply_settings_command(self, command: Callable[[], None]) -> None:
        self._apply_settings_button.configure(command=command)

    def set_load_settings_command(self, command: Callable[[], None]) -> None:
        self._load_settings_button.configure(command=command)

    def set_apply_settings_button_enabled(self, enabled: bool) -> None:
        self._apply_settings_button.configure(state=ttk.NORMAL if enabled else ttk.DISABLED)

    @property
    def settings_form_slot(self) -> View:
        return self._settings_form_slot # type: ignore

