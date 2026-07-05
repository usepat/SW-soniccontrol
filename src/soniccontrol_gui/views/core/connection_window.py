import asyncio
import contextlib
from enum import Enum
import os
from pathlib import Path
from typing import Any, Awaitable, Callable, Coroutine, Dict, List, Optional
from async_tkinter_loop import async_handler
import ttkbootstrap as ttk
import tkinter as tk

from sonic_protocol.python_parser import commands
from sonic_protocol.schema import DeviceType
from soniccontrol.app_config import APP_CONFIG
from soniccontrol.fw_device.fw_device_info import FwDeviceInfo
from soniccontrol.fw_device import create_connection_to_device, create_device_discovery, redetect_connection
from soniccontrol.network.connection import RemoteServerConnection
from soniccontrol_gui.plugins.device_plugin import DevicePluginRegistry
from soniccontrol_gui.plugins.ui_plugin import UIPluginRegistry, UIPluginSlotComponent
from soniccontrol_gui.ui_component import TopLevelWindow
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import View
from soniccontrol.fw_device.connection import CLIConnection, Connection, ModbusConnection
from soniccontrol.sonic_device import SonicDevice
from soniccontrol.logger.utils import create_logger_for_connection
from soniccontrol.modbus_defaults import DEFAULT_MODBUS_BAUDRATE
from soniccontrol_gui.utils.animator import Animator, DotAnimationSequence, load_animation
from soniccontrol_gui.constants import sizes, style, ui_labels, files
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.views.core.device_window import DeviceWindow, RescueWindow
from soniccontrol_gui.resources import images
from soniccontrol_gui.widgets.message_box import DialogOptions, MessageBox
from soniccontrol.communication.serial_communicator import SerialCommunicator
from soniccontrol.communication.modbus_communicator import ModbusCommunicator
from soniccontrol.builder import DeviceBuilder, StartupMode


class ConnectionMode(Enum):
    DEFAULT = "default"
    LEGACY_CRYSTAL = "legacy_crystal"
    CONFIGURATOR = "configurator"
    DIAGNOSTICS_TOOL = "diagnostics_tool"


CONNECTION_MODE_ENV_VAR = "SONICCONTROL_CONNECTION_MODES"


CONNECTION_MODE_LABELS = {
    ConnectionMode.DEFAULT: ui_labels.CONNECTION_MODE_DEFAULT_LABEL,
    ConnectionMode.LEGACY_CRYSTAL: ui_labels.IS_LEGACY_DEVICE_LABEL,
    ConnectionMode.CONFIGURATOR: ui_labels.CONNECTION_MODE_CONFIGURATOR_LABEL,
    ConnectionMode.DIAGNOSTICS_TOOL: ui_labels.CONNECTION_MODE_DIAGNOSTICS_TOOL_LABEL,
}

CONNECTION_MODE_BY_LABEL = {
    label: mode for mode, label in CONNECTION_MODE_LABELS.items()
}


def get_enabled_connection_modes() -> List[ConnectionMode]:
    configured_modes = os.environ.get(CONNECTION_MODE_ENV_VAR)
    if not configured_modes:
        return list(ConnectionMode)

    enabled_modes: List[ConnectionMode] = []
    for configured_mode in configured_modes.split(","):
        normalized_mode = configured_mode.strip().lower()
        if not normalized_mode:
            continue
        try:
            enabled_modes.append(ConnectionMode(normalized_mode))
        except ValueError:
            continue

    if enabled_modes:
        return enabled_modes

    return [ConnectionMode.DEFAULT, ConnectionMode.LEGACY_CRYSTAL]

class DeviceConnectionClass:
    def __init__(self, device_window : DeviceWindow, connection : Connection, startup_mode: StartupMode = StartupMode.DEFAULT):
        self._device_window = device_window
        self._connection = connection
        self._startup_mode = startup_mode


class DeviceWindowManager:
    MODBUS_READY_PROBE_ATTEMPTS = 10
    MODBUS_READY_PROBE_DELAY_S = 0.25
    MODBUS_CONNECT_RETRY_ATTEMPTS = 5

    def __init__(self, root):
        self._root = root
        self._id_device_window_counter = 0
        self._opened_device_windows: Dict[int, DeviceConnectionClass] = {}
        self._attempt_reconnect_callback: Optional[Callable[..., Awaitable[None]]] = None

    async def _open_rescue_window(self, sonicamp: SonicDevice, connection : Connection) -> DeviceWindow:
        device_window = RescueWindow(sonicamp, self._root, connection.connection_name)
        await self._open_device_window(device_window, connection)
        
        return device_window
    
    async def _open_device_window(self, device_window: DeviceWindow, connection : Connection, is_legacy_device: bool = False, startup_mode: StartupMode = StartupMode.DEFAULT):
        device_window._view.focus_set()  # grab focus and bring window to front
        self._id_device_window_counter += 1
        device_window_id = self._id_device_window_counter
        self._opened_device_windows[device_window_id] = DeviceConnectionClass(device_window, connection, startup_mode)
        device_window.subscribe(
            DeviceWindow.CLOSE_EVENT, lambda _: self._opened_device_windows.pop(device_window_id) #type: ignore
        )
        device_window.subscribe(
            DeviceWindow.RECONNECT_EVENT, lambda _: asyncio.create_task(self._attempt_reconnect_callback(connection, is_legacy_device, startup_mode)) #type: ignore
        ) 
        device_window.view.root.update_idletasks()
        await device_window.wait_finished_loading()  
        device_window.start_background_tasks()
        device_window.view.root.update_idletasks()

        return device_window
        

    async def attempt_reconnection(self, connection: Connection, is_legacy_device: bool = False, startup_mode: StartupMode = StartupMode.DEFAULT) -> DeviceWindow:
        try:
            new_connection = await redetect_connection(connection)
        except asyncio.TimeoutError:
            raise ConnectionError("Could not reconnect to the device")
        else:
            return await self.attempt_connection(new_connection, is_legacy_device, startup_mode)

        
    async def attempt_connection(self, connection: Connection, is_legacy_device: bool = False, startup_mode: StartupMode = StartupMode.DEFAULT) -> DeviceWindow:
        logger = create_logger_for_connection(connection.connection_name, files.LOG_DIR)
        logger.debug("Established serial connection")

        protocol_factories = { plugin.device_type: plugin.protocol_factory for plugin in DevicePluginRegistry.get_device_plugins() }
        device_builder = DeviceBuilder(protocol_factories=protocol_factories, logger=logger)
        modbus_retry_count = 0

        while True:
            try:
                logger.debug("Build SonicDevice for device")
                if is_legacy_device:
                    sonicamp = await device_builder.build_legacy_crystal(connection)
                elif startup_mode == StartupMode.CONFIGURATOR and not isinstance(connection, (CLIConnection, ModbusConnection)):
                    sonicamp = await device_builder.build_configurator(connection, try_deduce_protocol_used=True)
                elif startup_mode == StartupMode.DIAGNOSTICS_TOOL and not isinstance(connection, (CLIConnection, ModbusConnection)):
                    sonicamp = await device_builder.build_diagnostics_tool(connection, try_deduce_protocol_used=True)
                elif isinstance(connection, ModbusConnection):
                    communicator = ModbusCommunicator(logger=logger) # type: ignore
                    await communicator.open_communication(connection)
                    sonicamp = await device_builder.build_amp(communicator, try_deduce_protocol_used=True)
                else:
                    communicator = SerialCommunicator(logger=logger) # type: ignore
                    await communicator.open_communication(connection)
                    sonicamp = await device_builder.build_amp(communicator, try_deduce_protocol_used=True)
                break
            except Exception as e:
                logger.error(e)

                if isinstance(connection, ModbusConnection):
                    modbus_retry_count += 1
                    if modbus_retry_count < self.MODBUS_CONNECT_RETRY_ATTEMPTS:
                        logger.warning(
                            "Modbus connection attempt %s/%s failed, retrying automatically: %s",
                            modbus_retry_count,
                            self.MODBUS_CONNECT_RETRY_ATTEMPTS,
                            e,
                        )
                        await asyncio.sleep(self.MODBUS_READY_PROBE_DELAY_S)
                        continue

                message = ui_labels.COULD_NOT_CONNECT_MESSAGE.format(str(e))
                message_box = MessageBox.show_yes_no(self._root, message)
                user_answer: Optional[DialogOptions] = await message_box.wait_for_answer()
                if user_answer is None or user_answer == DialogOptions.NO:
                    raise asyncio.CancelledError()

                if isinstance(connection, ModbusConnection):
                    modbus_retry_count = 0
                    continue

                communicator = SerialCommunicator(logger=logger) # type: ignore
                await communicator.open_communication(connection)
                sonicamp = await device_builder.build_amp(communicator, try_deduce_protocol_used=False)
                break

        # TODO: Maybe we should move this into a plugin
        device_type = sonicamp.info.device_type
        if device_type in [DeviceType.MVP_WORKER, DeviceType.DESCALE, DeviceType.CRYSTAL, DeviceType.UNKNOWN]:
            # some devices are automatically in default routine.
            # To force them out of that, send the !sonic_force command
            await sonicamp.stop_running_processes()
            await self._wait_for_modbus_ready(sonicamp)
        
        if device_type != DeviceType.UNKNOWN:
            logger.info("Created device successfully, open device window")

            device_plugin = next((plugin for plugin in DevicePluginRegistry.get_device_plugins() if plugin.device_type == device_type), None)
            assert device_plugin is not None, f"No plugin found for the device type {device_type.name}"

            device_window = device_plugin.window_factory(sonicamp, self._root, connection.connection_name, is_legacy_device=is_legacy_device)
            window = await self._open_device_window(device_window, connection, is_legacy_device=is_legacy_device, startup_mode=startup_mode)
        else:
            window = await self._open_rescue_window(sonicamp, connection)
        
        return window

    async def _wait_for_modbus_ready(self, device: SonicDevice) -> None:
        if not isinstance(device.communicator, ModbusCommunicator):
            return

        last_error: Exception | None = None
        for attempt in range(1, self.MODBUS_READY_PROBE_ATTEMPTS + 1):
            answer = await device.execute_command(
                commands.GetProtocol(),
                raise_exception=False,
                disconnect_on_exception=False,
                should_log=False,
            )
            if answer.valid:
                return

            last_error = RuntimeError(answer.message)
            if attempt < self.MODBUS_READY_PROBE_ATTEMPTS:
                await asyncio.sleep(self.MODBUS_READY_PROBE_DELAY_S)

        if last_error is not None:
            raise last_error


    def set_attempt_reconnect_callback(self, callback: Callable[..., Awaitable[None]]):
        self._attempt_reconnect_callback = callback


class ConnectionWindow(TopLevelWindow):
    @staticmethod
    def _create_window_opened_future() -> asyncio.Future[DeviceWindow]:
        future = asyncio.get_event_loop().create_future()

        def _consume_exception(done_future: asyncio.Future[DeviceWindow]) -> None:
            if done_future.cancelled():
                return
            with contextlib.suppress(Exception):
                done_future.exception()

        future.add_done_callback(_consume_exception)
        return future

    def __init__(self, simulation_exe_path: Optional[Path] = None):        
        show_simulation_button = simulation_exe_path is not None or APP_CONFIG.remote_server_url is not None
        self._view: ConnectionWindowView = ConnectionWindowView(show_simulation_button)
        
        if simulation_exe_path:
            simulation_exe_path = simulation_exe_path.expanduser().resolve()
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
        animation_decorator = load_animation(animation)
        self._device_window_manager = DeviceWindowManager(self._view)
        
        def decorate_connection_func(connection_func: Callable[[Connection, bool, StartupMode], Coroutine[Any, Any, Any]]):
            # the wrapper is responsible for setting the future and is_connecting variable, as well as handling errors
            async def _wrapper(_connection: Connection, is_legacy_device: bool = False, startup_mode: StartupMode = StartupMode.DEFAULT):
                window_opened_future = self._create_window_opened_future()
                self._window_opened_future = window_opened_future

                try:
                    window = await connection_func(_connection, is_legacy_device, startup_mode)
                except asyncio.CancelledError as e:
                    if not window_opened_future.done():
                        window_opened_future.set_exception(e)
                    raise
                except Exception as e:
                    MessageBox.show_error(self.view.root, str(e))
                    if not window_opened_future.done():
                        window_opened_future.set_exception(e)
                else:
                    if not window_opened_future.done():
                        window_opened_future.set_result(window)
                finally:
                    self._is_connecting = False
            # the decorator is responsible for the controlling the loading animation
            return animation_decorator(_wrapper)

        self._is_connecting = False
        self._window_opened_future = self._create_window_opened_future()
        self._attempt_connection = decorate_connection_func(self._device_window_manager.attempt_connection)
        self._attempt_reconnection = decorate_connection_func(self._device_window_manager.attempt_reconnection)
        self._device_window_manager.set_attempt_reconnect_callback(self._attempt_reconnection)
        
        self._view.set_connect_via_url_button_command(self._on_connect_via_url)
        self._view.set_connect_to_simulation_button_command(self._on_connect_to_simulation)
        self._on_refresh_ports = async_handler(self._refresh_ports)
        self._view.set_refresh_button_command(self._on_refresh_ports)
        self._dev_infos: Dict[str, FwDeviceInfo] = {}
        self._loaded_ports = asyncio.Event()
        initial_refresh_task = asyncio.get_event_loop().create_task(self._refresh_ports())
        self.pass_loading_task(initial_refresh_task)


    async def _refresh_ports(self):
        self._loaded_ports.clear()
        device_discovery = create_device_discovery(APP_CONFIG.remote_server_url)
        dev_infos = await device_discovery.list_fw_device_infos(
            include_disks=False,
            include_unverified_ttys=True,
        )
        self._dev_infos = { dev_info.display_name: dev_info for dev_info in dev_infos }
        self._view.set_ports(list(self._dev_infos.keys()))
        self._loaded_ports.set()

    async def wait_until_window_loaded(self):
        window_opened_future = self._window_opened_future
        await window_opened_future
        return window_opened_future.result()


    @async_handler
    async def _on_connect_via_url(self):
        assert (not self._is_connecting), "already connecting"
        
        dev_display_name = self._view.get_dev_name()
        if dev_display_name == '':
            raise ValueError("No port selected")
        self._is_connecting = True

        baudrate = DEFAULT_MODBUS_BAUDRATE

        
        # assures ports were already loaded, needed for tests
        await self._loaded_ports.wait()

        dev_info = self._dev_infos[dev_display_name]
        # force_remove_connection is only used for remote devices at the moment. But may change in the future
        connection = create_connection_to_device(dev_info, baudrate, force_remove_connection=self._on_connection_already_open, is_modbus=self._view.is_modbus_device)
        
        await self._attempt_connection(connection, self._view.is_legacy_device, self._view.startup_mode)

    @async_handler 
    async def _on_connect_to_simulation(self):
        assert (not self._is_connecting)
        assert self._simulation_exe_path is not None
        self._is_connecting = True

        bin_file = self._simulation_exe_path 
        connection_name = "simulation"
        args: List[str] = []
        if self._view.startup_mode == StartupMode.CONFIGURATOR:
            args.append("--start-configurator=true")
        elif self._view.startup_mode == StartupMode.DIAGNOSTICS_TOOL:
            args.append("--force-start-diagnostics-tool")
        if self._view.use_firmware_gui:
            args.append("--gui=true")
        if self._view.profile != "none":
            args.append(f"--profile={self._view.profile}")
        if len(self._view.simulation_cmd_args) != 0:
            args.extend(self._view.simulation_cmd_args.split(" "))
  

        if APP_CONFIG.remote_server_url is None:
            connection = CLIConnection(connection_name, None, bin_file=bin_file, cmd_args=args)
        else:
            connection = RemoteServerConnection(
                connection_name, None, APP_CONFIG.remote_server_url, 
                force_remove_connection=True, port="simulation", cmd_args=args)
        
        await self._attempt_connection(connection, self._view.is_legacy_device, self._view.startup_mode)


    async def _on_connection_already_open(self) -> bool:
        msg_box = MessageBox.show_yes_no(self.view.root, ui_labels.ERROR_MSG_CONNECTION_ALREADY_OPEN)
        answer = await msg_box.wait_for_answer()
        if answer is None:
            return False
        return answer == DialogOptions.YES
    

class ConnectionWindowView(ttk.Window, View):
    def __init__(self, show_simulation_button: bool, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        window_name: str = "connection"
        enabled_connection_modes = get_enabled_connection_modes()
        enabled_connection_mode_labels = [CONNECTION_MODE_LABELS[mode] for mode in enabled_connection_modes]
        default_connection_mode = (
            ConnectionMode.DEFAULT if ConnectionMode.DEFAULT in enabled_connection_modes else enabled_connection_modes[0]
        )

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
        self._connection_mode = tk.StringVar(self, CONNECTION_MODE_LABELS[default_connection_mode])
        self._connection_mode_menue = ttk.Combobox(
            self._url_connection_frame, 
            textvariable=self._connection_mode,
            style=ttk.DARK,
            state=ttk.READONLY,
            values=enabled_connection_mode_labels,
        )
        WidgetRegistry.register_widget(self._connection_mode_menue, "connection_mode_combobox", window_name)

        self._is_modbus_device = tk.BooleanVar()
        self._is_modbus_device_box = tk.Checkbutton(
            self._url_connection_frame, 
            text=ui_labels.IS_MODBUS_DEVICE_LABEL,
            variable=self._is_modbus_device, 
            onvalue=1, 
            offvalue=0
        )
        WidgetRegistry.register_widget(self._is_modbus_device_box, "is_modbus_device_box", window_name)

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
            values=["postman", "worker", "descale", "diagnostics_tool", "none"]
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
        self._connection_mode_menue.pack(side=ttk.LEFT, padx=sizes.SMALL_PADDING)
        self._is_modbus_device_box.pack(side=ttk.LEFT, padx=sizes.SMALL_PADDING)
        if show_simulation_button:
            self._simulation_frame.pack(side=ttk.BOTTOM, fill=ttk.X, padx=sizes.SMALL_PADDING, pady=sizes.MEDIUM_PADDING)
            self._connect_to_simulation_button.pack(side=ttk.LEFT, fill=ttk.X, expand=True, padx=sizes.SMALL_PADDING)
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
        return self.connection_mode == ConnectionMode.LEGACY_CRYSTAL
    
    @property
    def is_modbus_device(self) -> bool:
        return self._is_modbus_device.get()
    
    @property
    def connection_mode(self) -> ConnectionMode:
        return CONNECTION_MODE_BY_LABEL[self._connection_mode.get()]

    @property
    def startup_mode(self) -> StartupMode:
        if self.connection_mode == ConnectionMode.CONFIGURATOR:
            return StartupMode.CONFIGURATOR
        if self.connection_mode == ConnectionMode.DIAGNOSTICS_TOOL:
            return StartupMode.DIAGNOSTICS_TOOL
        return StartupMode.DEFAULT
    
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

    def get_dev_name(self) -> str:
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
