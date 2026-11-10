import asyncio
import copy
from collections.abc import Callable

from async_tkinter_loop import async_handler
import attrs
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame

from sonic_protocol.field_names import EFieldName
from sonic_protocol.python_parser import commands
from sonic_protocol.schema import DeviceType, SIPrefix, Signal
from sonic_protocol.si_unit import AbsoluteFrequencySIVar, cls_converter, DescaleGainSIVar, GainSIVar, SwfSIVar
from soniccontrol.sonic_device import SonicDevice
from soniccontrol.utils.events import PropertyChangeEvent
from soniccontrol_gui.constants import sizes, ui_labels
from soniccontrol_gui.resources import images
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.debounce_job import DebounceJob
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import TabView, View
from soniccontrol_gui.views.core.app_state import ExecutionState
from soniccontrol_gui.widgets.form_widget import FormWidget

@attrs.define
class TransducerState:
    """Configuration data for the home view controls."""
    frequency: AbsoluteFrequencySIVar = attrs.field(
        converter=cls_converter(AbsoluteFrequencySIVar),
        factory=lambda: AbsoluteFrequencySIVar(100000),
        metadata={"field_view_kwargs": {"use_scale": True, "use_spinbox": True}}                                        
    )
    signal: bool = attrs.field(default=False, metadata={"field_view_kwargs":{"bootstyle": "round-toggle" }})
    gain: GainSIVar = attrs.field(
        converter=cls_converter(GainSIVar),
        factory=lambda: GainSIVar(value=1),
        metadata={"field_view_kwargs": {"use_scale": True, "use_spinbox": True}}                                        
    )

@attrs.define
class DescaleTransducerState:
    """Configuration data for the home view controls."""
    swf: SwfSIVar = attrs.field(
        converter=cls_converter(SwfSIVar),
        factory=lambda: SwfSIVar(5),
        metadata={"field_view_kwargs": {"use_scale": True, "use_spinbox": True}}                                        
    )
    signal: bool = attrs.field(default=False, metadata={"field_view_kwargs":{"bootstyle": "round-toggle" }})
    gain: DescaleGainSIVar = attrs.field(
        converter=cls_converter(DescaleGainSIVar),
        factory=lambda: DescaleGainSIVar(value=1),
        metadata={"field_view_kwargs": {"use_scale": True, "use_spinbox": True}}                                        
    )


class Home(UIComponent):
    def __init__(self, parent: UIComponent, device: SonicDevice):
        self._device = device
        # Initialize home configuration
        if device.info.device_type == DeviceType.DESCALE:
            self._config = DescaleTransducerState()
            self._config_old = DescaleTransducerState()
        else:
            self._config = TransducerState()
            self._config_old = TransducerState()

        
        self._model_sync_lock = asyncio.Lock()
        self._auto_send_enabled = True
        self._programmatic_form_update = False
        self._initial_device_state_loaded = False
        
        self._view = HomeView(parent.view)
        super().__init__(parent, self._view)

        self._info_frame = DeviceInfoFrame(self, self._view.info_frame_slot, "home", self._device) 
        self._model_change_debounce = DebounceJob(self._sync_changed_model, self._view)
        # Create the form widget for the configuration
        self._form_widget = FormWidget(
            self, 
            self._view.form_slot, 
            "Home Controls", 
            self._config.__class__, 
            "home",
            model_dict=attrs.asdict(self._config),
            use_scroll=False,
            model_change_callback=self._on_form_model_changed,
        )
        self._apply_config_state(self._config)

        self._view.set_auto_send_button_command(self._toggle_auto_send)
        self._view.set_send_button_command(self._on_send_pressed)
        self._view.set_send_button_enabled(not self._auto_send_enabled)
        self._view.after_idle(async_handler(self._fetch_device_transducer_state))

    def _on_form_model_changed(self, _: dict, **kwargs) -> None:
        if self._programmatic_form_update:
            return
        if not self._initial_device_state_loaded:
            return
        if self._auto_send_enabled:
            if kwargs.get("flush"):
                self._sync_changed_model()
            else:
                self._model_change_debounce()

    def _apply_config_state(self, state: TransducerState | DescaleTransducerState) -> None:
        # Keep UI form model and both config snapshots aligned and detached.
        self._programmatic_form_update = True
        try:
            self._form_widget.attrs_object = copy.deepcopy(state)
        finally:
            self._programmatic_form_update = False

        self._config = copy.deepcopy(state)
        self._config_old = copy.deepcopy(state)

    async def _fetch_device_transducer_state(self) -> None:
        answer = await self._device.get_update()
        try:
            if not answer.is_valid:
                return

            if self._device.info.device_type == DeviceType.DESCALE:
                state = DescaleTransducerState(
                    swf=answer[EFieldName.SWF],
                    gain=answer[EFieldName.GAIN],
                    signal=answer[EFieldName.SIGNAL] == Signal.ON,
                )
            else:
                state = TransducerState(
                    frequency=answer[EFieldName.FREQUENCY],
                    gain=answer[EFieldName.GAIN],
                    signal=answer[EFieldName.SIGNAL] == Signal.ON,
                )

            async with self._model_sync_lock:
                self._apply_config_state(state)
        finally:
            self._initial_device_state_loaded = True
        

    def _collect_changed_fields(self, config: TransducerState | DescaleTransducerState) -> list[str]:
        changed_fields: list[str] = []
        if isinstance(config, DescaleTransducerState):
            assert isinstance(self._config_old, DescaleTransducerState)
            if int(config.swf.to_prefix(SIPrefix.NONE)) != int(self._config_old.swf.to_prefix(SIPrefix.NONE)):
                changed_fields.append("swf")
            if config.gain.to_prefix(SIPrefix.NONE) != self._config_old.gain.to_prefix(SIPrefix.NONE):
                changed_fields.append("gain")
            if config.signal != self._config_old.signal:
                changed_fields.append("signal")
            return changed_fields

        assert isinstance(config, TransducerState)
        assert isinstance(self._config_old, TransducerState)
        if int(config.frequency.to_prefix(SIPrefix.NONE)) != int(self._config_old.frequency.to_prefix(SIPrefix.NONE)):
            changed_fields.append("frequency")
        if config.gain.to_prefix(SIPrefix.NONE) != self._config_old.gain.to_prefix(SIPrefix.NONE):
            changed_fields.append("gain")
        if config.signal != self._config_old.signal:
            changed_fields.append("signal")
        return changed_fields

    @async_handler
    async def _sync_changed_model(self) -> None:
        async with self._model_sync_lock:
            if not self._form_widget.valid:
                return
            config = self._form_widget.attrs_object
            changed_fields: list[str] = []
            if isinstance(config, DescaleTransducerState):
                assert isinstance(self._config_old, DescaleTransducerState)
                swf = int(config.swf.to_prefix(SIPrefix.NONE))
                if swf != int(self._config_old.swf.to_prefix(SIPrefix.NONE)):
                    await self._device.execute_command(commands.SetSwf(swf))
                    self._config_old.swf = copy.deepcopy(config.swf)
                    changed_fields.append("swf")
            else:
                assert isinstance(config, TransducerState)
                assert isinstance(self._config_old, TransducerState)
                frequency = int(config.frequency.to_prefix(SIPrefix.NONE))
                if frequency != int(self._config_old.frequency.to_prefix(SIPrefix.NONE)):
                    await self._device.execute_command(commands.SetFrequency(frequency))
                    self._config_old.frequency = copy.deepcopy(config.frequency)
                    changed_fields.append("frequency")

            gain = config.gain.to_prefix(SIPrefix.NONE)
            if gain != self._config_old.gain.to_prefix(SIPrefix.NONE):
                await self._device.execute_command(commands.SetGain(gain))
                self._config_old.gain = copy.deepcopy(config.gain)
                changed_fields.append("gain")

            if config.signal != self._config_old.signal:
                if config.signal:
                    await self._device.set_signal_on()
                else:
                    await self._device.set_signal_off()
                self._config_old.signal = config.signal
                changed_fields.append("signal")

            for field_name in changed_fields:
                if field_name in self._form_widget.fields:
                    self._form_widget.flash_field_success(field_name)

    @async_handler
    async def _on_send_pressed(self) -> None:
        async with self._model_sync_lock:
            config = self._form_widget.attrs_object
            changed_fields = self._collect_changed_fields(config)
            if isinstance(config, DescaleTransducerState):
                assert isinstance(self._config_old, DescaleTransducerState)
                swf = int(config.swf.to_prefix(SIPrefix.NONE))
                await self._device.execute_command(commands.SetSwf(swf))
                self._config_old.swf = copy.deepcopy(config.swf)
            else:
                assert isinstance(config, TransducerState)
                assert isinstance(self._config_old, TransducerState)
                frequency = int(config.frequency.to_prefix(SIPrefix.NONE))
                await self._device.execute_command(commands.SetFrequency(frequency))
                self._config_old.frequency = copy.deepcopy(config.frequency)

            gain = config.gain.to_prefix(SIPrefix.NONE)
            await self._device.execute_command(commands.SetGain(gain))
            self._config_old.gain = copy.deepcopy(config.gain)
            if config.signal:
                await self._device.set_signal_on()
            else:
                await self._device.set_signal_off()
            self._config_old.signal = config.signal

            for field_name in changed_fields:
                if field_name in self._form_widget.fields:
                    self._form_widget.flash_field_success(field_name)

    def _toggle_auto_send(self) -> None:
        self._auto_send_enabled = not self._auto_send_enabled
        self._view._auto_send_button.config(text=ui_labels.MANUAL_SEND_LABEL if self._auto_send_enabled else ui_labels.AUTO_SEND_LABEL)
        self._view.set_send_button_enabled(not self._auto_send_enabled)


    def on_execution_state_changed(self, e: PropertyChangeEvent) -> None:
        execution_state: ExecutionState = e.new_value.execution_state
        self._info_frame.on_execution_state_changed(e)
        self._view.set_send_button_enabled(execution_state == ExecutionState.IDLE and self._auto_send_enabled)

    @property 
    def freq(self) -> int:
        return int(self._form_widget.attrs_object.frequency.to_prefix(SIPrefix.NONE))
    
    @property 
    def swf(self) -> int:
        return int(self._form_widget.attrs_object.swf.to_prefix(SIPrefix.NONE))
    
    @property
    def gain(self) -> int:
        return self._form_widget.attrs_object.gain.to_prefix(SIPrefix.NONE)
    
    @property 
    def signal(self) -> bool:
        return self._form_widget.attrs_object.signal


class HomeView(TabView):
    def __init__(self, master: View, *args, **kwargs) -> None:
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

        self._info_frame_slot = ttk.Frame(self._main_frame)

        # Control frame - contains the form and send button
        self._control_frame: ttk.LabelFrame = ttk.LabelFrame(
            self._main_frame, text=ui_labels.CONTROL_LABEL
        )
        
        # Form slot - this is where the FormWidget will be placed
        self._form_slot = ttk.Frame(self._control_frame)

        self._auto_send_button = ttk.Button(
            self._control_frame, text=ui_labels.MANUAL_SEND_LABEL
        )
        
        self._send_button = ttk.Button(
            self._control_frame, text=ui_labels.SEND_LABEL
        )
        WidgetRegistry.register_widget(self._send_button, "send_button", tab_name)

    @property
    def form_slot(self) -> ttk.Frame:
        return self._form_slot
    
    @property
    def info_frame_slot(self) -> View:
        return self._info_frame_slot #type: ignore

    def _initialize_publish(self) -> None:
        self._main_frame.pack(fill=ttk.BOTH, expand=True)
        
        self._info_frame_slot.pack(fill=ttk.X)
        self._control_frame.pack(fill=ttk.BOTH, expand=True, pady=(0, sizes.LARGE_PADDING), ipady=sizes.LARGE_PADDING)
        # Layout the form slot first - ensure it expands to use all available space
        self._form_slot.pack(side=ttk.LEFT, fill=ttk.BOTH, expand=True, padx=(sizes.LARGE_PADDING, sizes.MEDIUM_PADDING), pady=sizes.LARGE_PADDING)
        # Layout the send button on the right side (fixed size, not expanding)
        self._auto_send_button.pack(side=ttk.RIGHT, padx=(0, sizes.LARGE_PADDING), pady=sizes.LARGE_PADDING)
        self._send_button.pack(side=ttk.RIGHT, padx=(0, sizes.LARGE_PADDING), pady=sizes.LARGE_PADDING)

    def set_send_button_command(self, command: Callable[[], None]) -> None:
        self._send_button.configure(command=command)

    def set_auto_send_button_command(self, command: Callable[[], None]) -> None:
            self._auto_send_button.configure(command=command)

    def set_send_button_enabled(self, enabled: bool) -> None:
        self._send_button.configure(state=ttk.NORMAL if enabled else ttk.DISABLED)


class DeviceInfoFrame(UIComponent):
    def __init__(self, parent: UIComponent, parent_slot: View, parent_widget_name: str, device: SonicDevice):
        self._device = device
        
        self._view = DeviceInfoFrameView(parent_slot, parent_widget_name=parent_widget_name)
        super().__init__(parent, self._view)
        self._view.set_disconnect_button_command(self._on_disconnect_pressed)
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

    def on_execution_state_changed(self, e: PropertyChangeEvent) -> None:
        execution_state: ExecutionState = e.new_value.execution_state
        self._view.set_disconnect_button_enabled(execution_state != ExecutionState.NOT_RESPONSIVE)


class DeviceInfoFrameView(View):
    def __init__(self, master: View, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        widget_name = self.scoped_widget_name()

        # info frame - displays device type, protocol type, firmware type
        self._info_frame: ttk.LabelFrame = ttk.LabelFrame(
            self, text=ui_labels.INFO_LABEL
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
        WidgetRegistry.register_widget(self._device_type_label, "device_type_label", widget_name)
        WidgetRegistry.register_widget(self._firmware_version_label, "firmware_version_label", widget_name)
        WidgetRegistry.register_widget(self._protocol_version_label, "protocol_version_label", widget_name)
        WidgetRegistry.register_widget(self._disconnect_button, "disconnect_button", widget_name)

    def _initialize_publish(self) -> None:
        self.pack(fill=ttk.BOTH)
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

    def set_device_type(self, text: str) -> None:
        self._device_type_label.configure(text=ui_labels.DEVICE_TYPE_LABEL.format(text)) 

    def set_firmware_version(self, text: str) -> None:
        self._firmware_version_label.configure(text=ui_labels.FIRMWARE_VERSION_LABEL.format(text)) 

    def set_protocol_version(self, text: str) -> None:
        self._protocol_version_label.configure(text=ui_labels.PROTOCOL_VERSION_LABEL.format(text)) 

    def set_disconnect_button_command(self, command: Callable[[], None]) -> None:
        self._disconnect_button.configure(command=command)

    def set_disconnect_button_enabled(self, enabled: bool) -> None:
        self._disconnect_button.configure(state=ttk.NORMAL if enabled else ttk.DISABLED)