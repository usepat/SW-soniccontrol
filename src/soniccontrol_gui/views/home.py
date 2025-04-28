from typing import Callable
from async_tkinter_loop import async_handler
from ttkbootstrap.scrolled import ScrolledFrame
from sonic_protocol.defs import DeviceType
from sonic_protocol.python_parser import commands
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import TabView, View
from soniccontrol.sonic_device import SonicDevice

import ttkbootstrap as ttk

from soniccontrol.events import PropertyChangeEvent
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.views.core.app_state import ExecutionState
from soniccontrol_gui.resources import images
from soniccontrol_gui.constants import ui_labels, sizes


class Home(UIComponent):
    def __init__(self, parent: UIComponent, device: SonicDevice):
        self._device = device
        self._view = HomeView(parent.view, device_type=device.info.device_type)
        super().__init__(parent, self._view)
        self._view.set_disconnect_button_command(self._on_disconnect_pressed)
        self._view.set_send_button_command(self._on_send_pressed)
        self._initialize_info()

    def _initialize_info(self) -> None:
        device_type = self._device.info.device_type
        firmware_version = str(self._device.info.firmware_version)
        protocol_version = "v" + str(self._device.communicator.protocol.major_version)
        self._view.set_device_type(device_type.value)
        self._view.set_firmware_version(firmware_version)
        self._view.set_protocol_version(protocol_version)

    @async_handler
    async def _on_disconnect_pressed(self) -> None:
        await self._device.disconnect()

    @async_handler
    async def _on_send_pressed(self) -> None:
        freq = self._view.freq
        gain = self._view.gain
        signal = self._view.signal

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
        execution_state: ExecutionState = e.new_value
        self._view.set_disconnect_button_enabled(execution_state != ExecutionState.NOT_RESPONSIVE)
        self._view.set_send_button_enabled(execution_state == ExecutionState.IDLE)


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

        # Control Frame - Setting Frequency, Gain, Signal
        self._control_frame: ttk.Labelframe = ttk.Labelframe(
            self._main_frame, text=ui_labels.HOME_CONTROL_LABEL
        )
        freq_label = ui_labels.FREQUENCY
        if self.device_type == DeviceType.DESCALE:
            freq_label = ui_labels.SWITCHING_FREQUENCY
        self._freq_frame: ttk.LabelFrame = ttk.LabelFrame(
            self._control_frame, text=freq_label
        )
        self._freq: ttk.IntVar = ttk.IntVar(value=100000)
        self._freq_spinbox: ttk.Spinbox = ttk.Spinbox(
            self._freq_frame,
            #placeholder=ui_labels.FREQ_PLACEHOLDER,
            #scrolled_frame=self._main_frame,
            style=ttk.DARK,
            textvariable=self._freq
        )
        freq_min = 100000
        freq_max = 10000000
        if self.device_type == 'descale':
            freq_min = 0
            freq_max = 20
        self._freq_scale: ttk.Scale = ttk.Scale(
            self._freq_frame,
            orient=ttk.HORIZONTAL,
            style=ttk.SUCCESS,
            from_=freq_min,
            to=freq_max, # TODO: set correct values
            variable=self._freq
        )
        WidgetRegistry.register_widget(self._freq_spinbox, "frequency_entry", tab_name)

        self._signal_frame: ttk.LabelFrame = ttk.LabelFrame(
            self._control_frame, text=ui_labels.SIGNAL_LABEL
        )
        self._signal: ttk.BooleanVar = ttk.BooleanVar(value=False)
        self._signal_button: ttk.Checkbutton = ttk.Checkbutton(
            self._signal_frame,
            bootstyle="round-toggle", #type: ignore
            variable=self._signal
        )
        WidgetRegistry.register_widget(self._signal_button, "signal_button", tab_name)

        self._gain_frame: ttk.LabelFrame = ttk.LabelFrame(
            self._control_frame, text=ui_labels.GAIN
        )
        self._gain: ttk.IntVar = ttk.IntVar(value=0)
        self._gain_spinbox: ttk.Spinbox = ttk.Spinbox(
            self._gain_frame,
            style=ttk.DARK,
            textvariable=self._gain
        )
        self._gain_scale: ttk.Scale = ttk.Scale(
            self._gain_frame,
            orient=ttk.HORIZONTAL,
            style=ttk.SUCCESS,
            from_=0,
            to=150,
            variable=self._gain
        )
        WidgetRegistry.register_widget(self._gain_spinbox, "gain_entry", tab_name)


        self._send_button = ttk.Button(
            self._control_frame, text=ui_labels.SEND_LABEL
        )
        WidgetRegistry.register_widget(self._send_button, "send_button", tab_name)


    def _initialize_publish(self) -> None:
        self._main_frame.pack(fill=ttk.BOTH, expand=True)
        
        self._info_frame.pack(fill=ttk.X)
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

        self._control_frame.pack(fill=ttk.BOTH, expand=True)
        self._freq_frame.grid(
            row=0, 
            column=0, 
            padx=sizes.LARGE_PADDING, 
            pady=sizes.LARGE_PADDING, 
            sticky=ttk.NSEW
        )
        self._freq_spinbox.grid(
            row=0, 
            column=0, 
            padx=sizes.LARGE_PADDING, 
            pady=sizes.MEDIUM_PADDING, 
            sticky=ttk.EW
        )
        self._freq_scale.grid(
            row=1, 
            column=0, 
            padx=sizes.LARGE_PADDING, 
            pady=sizes.MEDIUM_PADDING, 
            sticky=ttk.EW
        )

        self._signal_frame.grid(
            row=1, 
            column=0, 
            padx=sizes.LARGE_PADDING, 
            pady=sizes.LARGE_PADDING, 
            sticky=ttk.NSEW
        )
        self._signal_button.grid(
            row=0, 
            column=0, 
            padx=sizes.LARGE_PADDING, 
            pady=sizes.MEDIUM_PADDING, 
            sticky=ttk.EW
        )

        self._gain_frame.grid(
            row=2, 
            column=0, 
            padx=sizes.LARGE_PADDING, 
            pady=sizes.LARGE_PADDING, 
            sticky=ttk.NSEW
        )
        self._gain_spinbox.grid(
            row=0, 
            column=0, 
            padx=sizes.LARGE_PADDING, 
            pady=sizes.MEDIUM_PADDING, 
            sticky=ttk.EW
        )
        self._gain_scale.grid(
            row=1, 
            column=0, 
            padx=sizes.LARGE_PADDING, 
            pady=sizes.MEDIUM_PADDING, 
            sticky=ttk.EW
        )

        self._send_button.grid(
            row=1, 
            column=1, 
            padx=sizes.LARGE_PADDING, 
            pady=sizes.LARGE_PADDING, 
            sticky=ttk.EW
        )

    @property 
    def freq(self) -> int:
        return self._freq.get()
    
    @property
    def gain(self) -> int:
        return self._gain.get()
    
    @property 
    def signal(self) -> bool:
        return self._signal.get()
    
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
