import asyncio
from pathlib import Path
from typing import Awaitable, Callable, Dict, List, Optional
from async_tkinter_loop import async_handler
import serial.tools.list_ports as list_ports
import ttkbootstrap as ttk
import tkinter as tk

from sonic_protocol.schema import DeviceType, Version
from soniccontrol_gui.plugins.device_plugin import DevicePluginRegistry
from soniccontrol_gui.plugins.ui_plugin import UIPluginRegistry, UIPluginSlotComponent, register_ui_plugins
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import View
from soniccontrol.builder import DeviceBuilder
from soniccontrol.communication.connection import CLIConnection, Connection, SerialConnection
from soniccontrol.sonic_device import SonicDevice
from soniccontrol.logging_utils import create_logger_for_connection
from soniccontrol_gui.utils.animator import Animator, DotAnimationSequence, load_animation
from soniccontrol_gui.constants import sizes, style, ui_labels, files
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.views.core.device_window import DeviceWindow, RescueWindow
from soniccontrol_gui.resources import images
from soniccontrol_gui.widgets.message_box import DialogOptions, MessageBox
from sonic_protocol.python_parser import commands as cmds
from soniccontrol.communication.serial_communicator import SerialCommunicator

class DeviceConnectionClass:
    def __init__(self, deviceWindow : DeviceWindow, connection : Connection):
        self._deviceWindow = deviceWindow
        self._connection = connection


class DeviceWindowManager:
    def __init__(self, root):
        self._root = root
        self._id_device_window_counter = 0
        self._opened_device_windows: Dict[int, DeviceConnectionClass] = {}
        self._attempt_connection_callback: Optional[Callable[[Connection], Awaitable[None]]] = None

    def open_rescue_window(self, sonicamp: SonicDevice, connection : Connection) -> DeviceWindow:
        device_window = RescueWindow(sonicamp, self._root, connection.connection_name)
        self._open_device_window(device_window, connection)
        
        return device_window
    
    def _open_device_window(self, device_window: DeviceWindow, connection : Connection, is_legacy_device: bool = False):
        device_window._view.focus_set()  # grab focus and bring window to front
        self._id_device_window_counter += 1
        device_window_id = self._id_device_window_counter
        self._opened_device_windows[device_window_id] = DeviceConnectionClass(device_window, connection)
        device_window.subscribe(
            DeviceWindow.CLOSE_EVENT, lambda _: self._opened_device_windows.pop(device_window_id) #type: ignore
        )
        device_window.subscribe(
            DeviceWindow.RECONNECT_EVENT, lambda _: asyncio.create_task(self._attempt_connection_callback(connection, is_legacy_device)) #type: ignore
        )    
        
    async def attempt_connection(self, connection: Connection, is_legacy_device: bool = False):
        logger = create_logger_for_connection(connection.connection_name, files.LOG_DIR)
        logger.debug("Established serial connection")

        protocol_factories = { plugin.device_type: plugin.protocol_factory for plugin in DevicePluginRegistry.get_device_plugins() }
        device_builder = DeviceBuilder(protocol_factories=protocol_factories, logger=logger)

        try:
            logger.debug("Build SonicDevice for device")
            if is_legacy_device:
                sonicamp = await device_builder.build_legacy_crystal(connection)
            else:
                communicator = SerialCommunicator(logger=logger) # type: ignore
                await communicator.open_communication(connection)
                sonicamp = await device_builder.build_amp(communicator, try_deduce_protocol_used=True)
        
        except Exception as e:
            logger.error(e)
            message = ui_labels.COULD_NOT_CONNECT_MESSAGE.format(str(e))
            message_box = MessageBox.show_yes_no(self._root, message)
            user_answer: Optional[DialogOptions] = await message_box.wait_for_answer()
            if user_answer is None or user_answer == DialogOptions.NO: 
                return
            
            communicator = SerialCommunicator(logger=logger) # type: ignore
            await communicator.open_communication(connection)
            sonicamp = await device_builder.build_amp(communicator, try_deduce_protocol_used=False)

        # TODO: Maybe we should move this into a plugin
        device_type = sonicamp.info.device_type
        if device_type in [DeviceType.MVP_WORKER, DeviceType.DESCALE, DeviceType.CRYSTAL, DeviceType.UNKNOWN]:
            # some devices are automatically in default routine.
            # To force them out of that, send the !sonic_force command
            if sonicamp.has_command(cmds.SetStop()):
                await sonicamp.execute_command(cmds.SetStop(), raise_exception=False)
            # We cant use SetOff for the crystal+ device because it is not ready yet
            if sonicamp.has_command(cmds.SetOff()) and not is_legacy_device:
                await sonicamp.execute_command(cmds.SetOff(), raise_exception=False)
            if sonicamp.has_command(cmds.SonicForce()):
                await sonicamp.execute_command(cmds.SonicForce(), raise_exception=False)
        
        if device_type != DeviceType.UNKNOWN:
            logger.info("Created device successfully, open device window")

            device_plugin = next((plugin for plugin in DevicePluginRegistry.get_device_plugins() if plugin.device_type == device_type), None)
            assert device_plugin is not None, f"No plugin found for the device type {device_type.name}"

            device_window = device_plugin.window_factory(sonicamp, self._root, connection.connection_name, is_legacy_device=is_legacy_device)
            self._open_device_window(device_window, connection)
        else:
            self.open_rescue_window(sonicamp, connection)


    def set_attempt_connection_callback(self, callback: Callable[[Connection], Awaitable[None]]):
        self._attempt_connection_callback = callback


class ConnectionWindow(UIComponent):
    def __init__(self, simulation_exe_path: Optional[Path] = None):
        #TODO move this somewhere else?
        register_ui_plugins()
        show_simulation_button = simulation_exe_path is not None
        self._view: ConnectionWindowView = ConnectionWindowView(show_simulation_button)
        
        self._simulation_exe_path = simulation_exe_path
        super().__init__(None, self._view)
        # Create and PLACE the plugin slot (tabs=True -> Notebook; False -> stacked)
        self._plugin_slot = UIPluginSlotComponent(
            self,
            [p for p in UIPluginRegistry.get_ui_plugins() if p.slot_name == self.__class__.__name__],
            master=self._view.plugins_container,
            tabs=True,  # or False if you want stacked
        )
        # Actually lay it out in the container
        self._plugin_slot.view.pack(fill=tk.BOTH, expand=True)
        # set animation decorator
        def set_loading_animation_frame(frame: str) -> None:
            self._view.loading_text = frame
        def on_animation_end() -> None:
            self._view.loading_text = ""
        animation = Animator(DotAnimationSequence("Connecting"), set_loading_animation_frame, 2., done_callback=on_animation_end)
        decorator = load_animation(animation)
        self._device_window_manager = DeviceWindowManager(self._view)
        
        async def _attempt_connection(_connection: Connection, is_legacy_device: bool = False):
            await self._device_window_manager.attempt_connection(_connection, is_legacy_device)

        self._is_connecting = False # Make this to asyncio Event if needed
        self._attempt_connection = decorator(_attempt_connection)
        self._device_window_manager.set_attempt_connection_callback(self._attempt_connection)
        
        self._view.set_connect_via_url_button_command(self._on_connect_via_url)
        self._view.set_connect_to_simulation_button_command(self._on_connect_to_simulation)
        self._view.set_refresh_button_command(self._refresh_ports)
        self._refresh_ports()

    @property
    def is_connecting(self) -> bool:
        return self._is_connecting
    
    @is_connecting.setter
    def is_connecting(self, value: bool):
        self._is_connecting = value
        self._view.enable_connect_via_url_button(not value)
        self._view.enable_connect_to_simulation_button(not value)

    def _refresh_ports(self):
        ports = [port.device for port in list_ports.comports()]
        self._view.set_ports(ports)

    @async_handler
    async def _on_connect_via_url(self):
        assert (not self.is_connecting)
        self._is_connecting = True

        url = self._view.get_url()
        baudrate = 9600

        connection = SerialConnection(url=url, baudrate=baudrate, connection_name=Path(url).name)
        await self._attempt_connection(connection, self._view.is_legacy_device)
        self._is_connecting = False

    @async_handler 
    async def _on_connect_to_simulation(self):
        assert (not self.is_connecting)
        assert self._simulation_exe_path is not None
        self._is_connecting = True

        bin_file = self._simulation_exe_path 
        args: List[str] = []
        if self._view.should_start_configurator:
            args.append("--start-configurator=true")
        if self._view.use_firmware_gui:
            args.append("--gui")
        if self._view.profile != "none":
            args.append(f"--profile={self._view.profile}")
        if len(self._view.simulation_cmd_args) != 0:
            args.extend(self._view.simulation_cmd_args.split(" "))
  

        connection = CLIConnection(bin_file=bin_file, connection_name = "simulation", cmd_args=args)
        await self._attempt_connection(connection)
        self._is_connecting = False


class ConnectionWindowView(ttk.Window, View):
    def __init__(self, show_simulation_button: bool, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        window_name: str = "connection"

        image = ImageLoader.load_image_resource(images.LOGO, sizes.LARGE_BUTTON_ICON_SIZE)
        self.iconphoto(True, image)

        self._url_connection_frame: ttk.Frame = ttk.Frame(self)
        self._refresh_button: ttk.Button = ttk.Button(
            self._url_connection_frame,
            image=ImageLoader.load_image_resource(
                images.REFRESH_ICON_GREY, sizes.BUTTON_ICON_SIZE
            ),
            style=style.SECONDARY_OUTLINE,
            compound=ttk.RIGHT,
        )
        self._port = tk.StringVar()
        self._ports_menue: ttk.Combobox = ttk.Combobox(
            self._url_connection_frame,
            textvariable=self._port,
            style=ttk.DARK,
            state=ttk.READONLY,
        )
        WidgetRegistry.register_widget(self._ports_menue, "ports_combobox", window_name)
        self._is_legacy_device = tk.BooleanVar()
        self._is_legacy_device_box = tk.Checkbutton(
            self._url_connection_frame, 
            text=ui_labels.IS_LEGACY_DEVICE_LABEL,
            variable=self._is_legacy_device, 
            onvalue=1, 
            offvalue=0
        )

        WidgetRegistry.register_widget(self._is_legacy_device_box, "is_legacy_device_box", window_name)
        self._connect_via_url_button: ttk.Button = ttk.Button(
            self._url_connection_frame,
            style=ttk.SUCCESS,
            text=ui_labels.CONNECT_LABEL,
        )
        WidgetRegistry.register_widget(self._connect_via_url_button, "connect_via_url_button", window_name)

        self._simulation_frame: ttk.Frame = ttk.Frame(self)

        self._connect_to_simulation_button: ttk.Button = ttk.Button(
            self._simulation_frame,
            style=ttk.SUCCESS,
            text=ui_labels.CONNECT_TO_SIMULATION_LABEL,
        )
        WidgetRegistry.register_widget(self._connect_to_simulation_button, "connect_to_simulation_button", window_name)

        self._should_start_configurator = tk.BooleanVar()
        self._start_configurator_box = tk.Checkbutton(
            self._simulation_frame, 
            text=ui_labels.START_CONFIGURATOR,
            variable=self._should_start_configurator, 
            onvalue=1, 
            offvalue=0
        )
        WidgetRegistry.register_widget(self._start_configurator_box, "start_configurator_box", window_name)

        self._use_firmware_gui = tk.BooleanVar()
        self._use_firmware_gui_box = tk.Checkbutton(
            self._simulation_frame, 
            text=ui_labels.USE_FIRMWARE_GUI,
            variable=self._use_firmware_gui, 
            onvalue=1, 
            offvalue=0
        )
        WidgetRegistry.register_widget(self._use_firmware_gui_box, "use_firmware_gui_box", window_name)


        self._simulation_cmd_args = tk.StringVar()
        self._simulation_cmd_args_entry = tk.Entry(self._simulation_frame, textvariable=self._simulation_cmd_args)
        WidgetRegistry.register_widget(self._simulation_cmd_args_entry, "simulation_cmd_args", window_name)

        self._profile = tk.StringVar(self, "none")
        self._profile_menue: ttk.Combobox = ttk.Combobox(
            self._simulation_frame,
            textvariable=self._profile,
            style=ttk.DARK,
            state=ttk.READONLY,
            values=["postman", "worker", "none"]
        )

        # --- plugin container (NEW) ---
        self.plugins_container = ttk.Frame(self)

        self._loading_text: ttk.StringVar = ttk.StringVar()
        self._loading_label: ttk.Label = ttk.Label(
            self,
            textvariable=self._loading_text
        )

        self._url_connection_frame.pack(side=ttk.TOP, fill=ttk.X, expand=True, pady=sizes.MEDIUM_PADDING)
        self._ports_menue.pack(
            side=ttk.LEFT, expand=True, fill=ttk.X, padx=sizes.SMALL_PADDING
        )
        self._refresh_button.pack(side=ttk.LEFT, padx=sizes.SMALL_PADDING)
        self._connect_via_url_button.pack(side=ttk.LEFT, padx=sizes.SMALL_PADDING)
        self._is_legacy_device_box.pack(side=ttk.LEFT, padx=sizes.SMALL_PADDING)
        if show_simulation_button:
            self._simulation_frame.pack(side=ttk.BOTTOM, fill=ttk.X, padx=sizes.SMALL_PADDING, pady=sizes.MEDIUM_PADDING)
            self._connect_to_simulation_button.pack(side=ttk.LEFT, fill=ttk.X, expand=True, padx=sizes.SMALL_PADDING)
            self._start_configurator_box.pack(side=ttk.RIGHT, padx=sizes.SMALL_PADDING)
            self._use_firmware_gui_box.pack(side=ttk.RIGHT, padx=sizes.SMALL_PADDING)
            self._profile_menue.pack(side=ttk.RIGHT, padx=sizes.SMALL_PADDING)
            self._simulation_cmd_args_entry.pack(side=ttk.RIGHT, padx=sizes.SMALL_PADDING)

        self._loading_label.pack(side=ttk.TOP, pady=sizes.MEDIUM_PADDING)

        # Place plugins_container between controls and loading
        self.plugins_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=4, pady=6)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    @async_handler
    async def on_close(self):
        # clean up
        try:
            self.root.grab_release()
        except tk.TclError:
            pass

        self.root.after_idle(self.root.destroy)
        await WidgetRegistry.clean_up()

    @property
    def loading_text(self) -> str:
        return self._loading_text.get()
    
    @property
    def is_legacy_device(self) -> bool:
        return self._is_legacy_device.get()
    
    @property
    def should_start_configurator(self) -> bool:
        return self._should_start_configurator.get()
    
    @property
    def use_firmware_gui(self) -> bool:
        return self._use_firmware_gui.get()
    
    @property
    def simulation_cmd_args(self) -> str:
        return self._simulation_cmd_args.get()
    
    @property 
    def profile(self) -> str:
        return self._profile.get()
    
    @loading_text.setter
    def loading_text(self, value: str) -> None:
        self._loading_text.set(value)

    def get_url(self) -> str:
        return self._port.get()

    def set_connect_via_url_button_command(self, command: Callable[[], None]) -> None:
        self._connect_via_url_button.configure(command=command)

    def set_connect_to_simulation_button_command(self, command: Callable[[], None]) -> None:
        self._connect_to_simulation_button.configure(command=command)

    def set_refresh_button_command(self, command: Callable[[], None]) -> None:
        self._refresh_button.configure(command=command)

    def set_ports(self, ports: List[str]) -> None:
        self._ports_menue.configure(values=ports)

    def enable_connect_via_url_button(self, enabled: bool) -> None:
        self._connect_via_url_button.configure(state=ttk.NORMAL if enabled else ttk.DISABLED)

    def enable_connect_to_simulation_button(self, enabled: bool) -> None:
        self._connect_to_simulation_button.configure(state=ttk.NORMAL if enabled else ttk.DISABLED)
