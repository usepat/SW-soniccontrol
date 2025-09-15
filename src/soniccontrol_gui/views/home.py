from typing import Callable
from async_tkinter_loop import async_handler
from ttkbootstrap.scrolled import ScrolledFrame
from sonic_protocol.schema import DeviceType, SIPrefix
from sonic_protocol.python_parser import commands
from soniccontrol_gui.ui_component import UIComponent
from sonic_protocol.si_unit import AbsoluteFrequencySIVar, GainSIVar
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import TabView, View
from soniccontrol.sonic_device import SonicDevice
from soniccontrol_gui.widgets.form_widget import FormWidget

import ttkbootstrap as ttk
import attrs

from soniccontrol.events import PropertyChangeEvent
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.views.core.app_state import ExecutionState
from soniccontrol_gui.resources import images
from soniccontrol_gui.constants import ui_labels, sizes

@attrs.define
class TransducerState:
    """Configuration data for the home view controls."""
    frequency: AbsoluteFrequencySIVar = attrs.field(default=AbsoluteFrequencySIVar(100000),
        metadata={"field_view_kwargs": {"use_scale": True, "use_spinbox": True}}                                        
    )
    signal: bool = attrs.field(default=False, metadata={"field_view_kwargs":{"bootstyle": "round-toggle" }})
    gain: GainSIVar = attrs.field(default=GainSIVar(value=0),
        metadata={"field_view_kwargs": {"use_scale": True, "use_spinbox": True}}                                        
    )



class Home(UIComponent):
    def __init__(self, parent: UIComponent, device: SonicDevice):
        self._device = device
        # Initialize home configuration
        self._config = TransducerState()
        # Adjust frequency range based on device type
        if device.info.device_type == DeviceType.DESCALE:
            self._config.frequency.value = 0
            # You can adjust min/max ranges here later
        
        self._view = HomeView(parent.view, device_type=device.info.device_type)
        super().__init__(parent, self._view)
        
        # Create the form widget for the configuration
        self._form_widget = FormWidget(
            self, 
            self._view.form_slot, 
            "Home Controls", 
            TransducerState, 
            model_dict=attrs.asdict(self._config),
            use_scroll=False
        )
        
        self._view.set_disconnect_button_command(self._on_disconnect_pressed)
        self._view.set_send_button_command(self._on_send_pressed)
        self._initialize_info()

    def _initialize_info(self) -> None:
        device_type = self._device.info.device_type
        firmware_version = str(self._device.info.firmware_version)
        protocol_version = str(self._device.info.protocol_version)
        self._view.set_device_type(device_type.value)
        self._view.set_firmware_version(firmware_version)
        self._view.set_protocol_version(protocol_version)

    @async_handler
    async def _on_disconnect_pressed(self) -> None:
        await self._device.disconnect()

    @async_handler
    async def _on_send_pressed(self) -> None:
        freq = self.freq
        gain = self.gain
        signal = self.signal

        if self._device.info.device_type == 'descale':
            await self._device.execute_command(commands.SetSwf(freq))
        else:
            await self._device.execute_command(commands.SetFrequency(freq))
        await self._device.execute_command(commands.SetGain(gain))
        if signal:
            await self._device.set_signal_on()
        else:
            await self._device.set_signal_off()

    def on_execution_state_changed(self, e: PropertyChangeEvent) -> None:
        execution_state: ExecutionState = e.new_value.execution_state
        self._view.set_disconnect_button_enabled(execution_state != ExecutionState.NOT_RESPONSIVE)
        self._view.set_send_button_enabled(execution_state == ExecutionState.IDLE)

    @property 
    def freq(self) -> int:
        return self._form_widget.attrs_object.frequency.to_prefix(SIPrefix.NONE)
    
    @property
    def gain(self) -> int:
        return self._form_widget.attrs_object.gain.to_prefix(SIPrefix.NONE)
    
    @property 
    def signal(self) -> bool:
        return self._form_widget.attrs_object.signal


class HomeView(TabView):
    def __init__(self, master: View, *args, **kwargs) -> None:
        if 'device_type' in kwargs:
            self.device_type = kwargs.pop('device_type')
        super().__init__(master, *args, **kwargs)

    @property
    def image(self) -> ttk.ImageTk.PhotoImage:
        return ImageLoader.load_image_resource(images.HOME_ICON_BLACK, sizes.TAB_ICON_SIZE)

    @property
    def tab_title(self) -> str:
        return ui_labels.HOME_LABEL
    
    def _initialize_children(self) -> None:
        tab_name = "home"
        self._main_frame: ScrolledFrame = ScrolledFrame(self, autohide=True)

        # info frame - displays device type, protocol type, firmware type
        self._info_frame: ttk.LabelFrame = ttk.LabelFrame(
            self._main_frame, text=ui_labels.INFO_LABEL
        )
        self._device_type_label = ttk.Label(
            self._info_frame, text=ui_labels.DEVICE_TYPE_LABEL.format("N/A")
        )
        self._firmware_version_label = ttk.Label(
            self._info_frame, text=ui_labels.FIRMWARE_VERSION_LABEL.format("N/A")
        )
        self._protocol_version_label = ttk.Label(
            self._info_frame, text=ui_labels.PROTOCOL_VERSION_LABEL.format("N/A")
        )
        self._disconnect_button = ttk.Button(
            self._info_frame, text=ui_labels.DISCONNECT_LABEL
        )
        WidgetRegistry.register_widget(self._device_type_label, "device_type_label", tab_name)
        WidgetRegistry.register_widget(self._firmware_version_label, "firmware_version_label", tab_name)
        WidgetRegistry.register_widget(self._protocol_version_label, "protocol_version_label", tab_name)
        WidgetRegistry.register_widget(self._disconnect_button, "disconnect_button", tab_name)

        # Control frame - contains the form and send button
        self._control_frame: ttk.LabelFrame = ttk.LabelFrame(
            self._main_frame, text=ui_labels.CONTROL_LABEL
        )
        
        # Form slot - this is where the FormWidget will be placed
        self._form_slot = ttk.Frame(self._control_frame)
        
        self._send_button = ttk.Button(
            self._control_frame, text=ui_labels.SEND_LABEL
        )
        WidgetRegistry.register_widget(self._send_button, "send_button", tab_name)

    @property
    def form_slot(self) -> ttk.Frame:
        return self._form_slot


    def _initialize_publish(self) -> None:
        self._main_frame.pack(fill=ttk.BOTH, expand=True)
        
        self._info_frame.pack(fill=ttk.X, pady=(0, sizes.MEDIUM_PADDING))
        self._device_type_label.grid(
            row=0, 
            column=0, 
            padx=sizes.LARGE_PADDING, 
            pady=sizes.MEDIUM_PADDING, 
            sticky=ttk.W
        )
        self._firmware_version_label.grid(
            row=1, 
            column=0, 
            padx=sizes.LARGE_PADDING, 
            pady=sizes.MEDIUM_PADDING, 
            sticky=ttk.W
        )
        self._protocol_version_label.grid(
            row=2, 
            column=0, 
            padx=sizes.LARGE_PADDING, 
            pady=sizes.MEDIUM_PADDING, 
            sticky=ttk.W
        )
        self._disconnect_button.grid(
            row=3, 
            column=0, 
            padx=sizes.LARGE_PADDING, 
            pady=sizes.MEDIUM_PADDING, 
            sticky=ttk.W
        )

        self._control_frame.pack(fill=ttk.BOTH, expand=True, pady=(0, sizes.LARGE_PADDING), ipady=sizes.LARGE_PADDING)
        
        # Layout the form slot first - ensure it expands to use all available space
        self._form_slot.pack(side=ttk.LEFT, fill=ttk.BOTH, expand=True, padx=(sizes.LARGE_PADDING, sizes.MEDIUM_PADDING), pady=sizes.LARGE_PADDING)
        
        # Layout the send button on the right side (fixed size, not expanding)
        self._send_button.pack(side=ttk.RIGHT, padx=(0, sizes.LARGE_PADDING), pady=sizes.LARGE_PADDING)

    def set_device_type(self, text: str) -> None:
        self._device_type_label.configure(text=ui_labels.DEVICE_TYPE_LABEL.format(text)) 

    def set_firmware_version(self, text: str) -> None:
        self._firmware_version_label.configure(text=ui_labels.FIRMWARE_VERSION_LABEL.format(text)) 

    def set_protocol_version(self, text: str) -> None:
        self._protocol_version_label.configure(text=ui_labels.PROTOCOL_VERSION_LABEL.format(text)) 

    def set_disconnect_button_command(self, command: Callable[[], None]) -> None:
        self._disconnect_button.configure(command=command)

    def set_send_button_command(self, command: Callable[[], None]) -> None:
        self._send_button.configure(command=command)

    def set_disconnect_button_enabled(self, enabled: bool) -> None:
        self._disconnect_button.configure(state=ttk.NORMAL if enabled else ttk.DISABLED)

    def set_send_button_enabled(self, enabled: bool) -> None:
        self._send_button.configure(state=ttk.NORMAL if enabled else ttk.DISABLED)
