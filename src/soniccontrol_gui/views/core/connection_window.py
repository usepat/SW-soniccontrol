import asyncio
from pathlib import Path
from typing import Awaitable, Callable, Dict, List, Optional, cast
from async_tkinter_loop import async_handler
import serial.tools.list_ports as list_ports
import ttkbootstrap as ttk
import tkinter as tk
from ttkbootstrap.dialogs.dialogs import Messagebox

from sonic_protocol.defs import Version
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import View
from soniccontrol.builder import DeviceBuilder
from soniccontrol.commands import CommandSetLegacy
from soniccontrol.communication.communicator_builder import CommunicatorBuilder
from soniccontrol.communication.connection_factory import CLIConnectionFactory, ConnectionFactory, SerialConnectionFactory
from soniccontrol.communication.communicator import Communicator
from soniccontrol.communication.serial_communicator import LegacySerialCommunicator
from soniccontrol.sonic_device import SonicDevice
from soniccontrol.logging import create_logger_for_connection
from soniccontrol_gui.utils.animator import Animator, DotAnimationSequence, load_animation
from soniccontrol_gui.constants import sizes, style, ui_labels, files
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.views.core.device_window import DeviceWindow, KnownDeviceWindow, RescueWindow
from soniccontrol_gui.resources import images

class DeviceConnectionClasses:
    def __init__(self, deviceWindow : DeviceWindow, connectionFactory : ConnectionFactory):
        self._deviceWindow = deviceWindow
        self._connectionFactory = connectionFactory


class DeviceWindowManager:
    def __init__(self, root):
        self._root = root
        self._id_device_window_counter = 0
        self._opened_device_windows: Dict[int, DeviceConnectionClasses] = {}
        self._attempt_connection_callback: Optional[Callable[[ConnectionFactory], Awaitable[None]]] = None

    def open_rescue_window(self, sonicamp: SonicDevice, connection_factory : ConnectionFactory) -> DeviceWindow:
        device_window = RescueWindow(sonicamp, self._root, connection_factory.connection_name)
        self._open_device_window(device_window, connection_factory)
        
        return device_window

    def open_known_device_window(self, sonicamp: SonicDevice, connection_factory : ConnectionFactory) -> DeviceWindow:
        device_window = KnownDeviceWindow(sonicamp, self._root, connection_factory.connection_name)
        self._open_device_window(device_window, connection_factory)
        return device_window
    
    def _open_device_window(self, device_window: DeviceWindow, connection_factory : ConnectionFactory):
        device_window._view.focus_set()  # grab focus and bring window to front
        self._id_device_window_counter += 1
        device_window_id = self._id_device_window_counter
        self._opened_device_windows[device_window_id] = DeviceConnectionClasses(device_window, connection_factory)
        device_window.subscribe(
            DeviceWindow.CLOSE_EVENT, lambda _: self._opened_device_windows.pop(device_window_id) #type: ignore
        )
        device_window.subscribe(
            DeviceWindow.RECONNECT_EVENT, lambda _: asyncio.create_task(self._attempt_connection_callback(connection_factory)) #type: ignore
        )    
        
    async def attempt_connection(self, connection_factory: ConnectionFactory):
        logger = create_logger_for_connection(connection_factory.connection_name, files.LOG_DIR)
        logger.debug("Established serial connection")

        try:
            serial, commands = await CommunicatorBuilder.build(
                connection_factory,
                logger=logger
            )
            logger.debug("Build SonicDevice for device")
            sonicamp = await DeviceBuilder().build_amp(comm=serial, commands=commands, logger=logger)
            await sonicamp.communicator.connection_opened.wait()
        except ConnectionError as e:
            logger.error(e)
            message = ui_labels.COULD_NOT_CONNECT_MESSAGE.format(str(e))
            user_answer: Optional[str] = cast(Optional[str], Messagebox.yesno(message))
            if user_answer is None or user_answer == "No": 
                return
            
            serial: Communicator = LegacySerialCommunicator(logger=logger) #type: ignore
            commands = CommandSetLegacy(serial)
            await serial.open_communication(connection_factory)
            sonicamp = await DeviceBuilder().build_amp(comm=serial, commands=commands, logger=logger, try_deduce_protocol=False)
            self.open_rescue_window(sonicamp, connection_factory)
        except Exception as e:
            logger.error(e)
            Messagebox.show_error(str(e))
        else:
            logger.info("Created device successfully, open device window")
            if sonicamp.info.protocol_version >= Version(1, 0, 0):
                self.open_known_device_window(sonicamp, connection_factory)
            else:
                self.open_rescue_window(sonicamp, connection_factory)

    def set_attempt_connection_callback(self, callback: Callable[[ConnectionFactory], Awaitable[None]]):
        self._attempt_connection_callback = callback


class ConnectionWindow(UIComponent):
    def __init__(self, simulation_exe_path: Optional[Path] = None):
        show_simulation_button = simulation_exe_path is not None
        self._view: ConnectionWindowView = ConnectionWindowView(show_simulation_button)
        self._simulation_exe_path = simulation_exe_path
        super().__init__(None, self._view)

        # set animation decorator
        def set_loading_animation_frame(frame: str) -> None:
            self._view.loading_text = frame
        def on_animation_end() -> None:
            self._view.loading_text = ""
        animation = Animator(DotAnimationSequence("Connecting"), set_loading_animation_frame, 2., done_callback=on_animation_end)
        decorator = load_animation(animation)
        self._device_window_manager = DeviceWindowManager(self._view)
        
        async def _attempt_connection(connection_factory: ConnectionFactory):
            await self._device_window_manager.attempt_connection(connection_factory)

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

        connection_factory = SerialConnectionFactory(url=url, baudrate=baudrate, connection_name=Path(url).name)
        await self._attempt_connection(connection_factory)
        self._is_connecting = False

    @async_handler 
    async def _on_connect_to_simulation(self):
        assert (not self.is_connecting)
        assert self._simulation_exe_path is not None

        self._is_connecting = True

        bin_file = self._simulation_exe_path 

        connection_factory = CLIConnectionFactory(bin_file=bin_file, connection_name = "simulation")

        await self._attempt_connection(connection_factory)
        self._is_connecting = False


class ConnectionWindowView(ttk.Window, View):
    def __init__(self, show_simulation_button: bool, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        ImageLoader(self)

        window_name: str = "connection"

        self.iconphoto(True, ImageLoader.load_image_resource(images.LOGO, sizes.LARGE_BUTTON_ICON_SIZE))

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

        self._connect_via_url_button: ttk.Button = ttk.Button(
            self._url_connection_frame,
            style=ttk.SUCCESS,
            text=ui_labels.CONNECT_LABEL,
        )
        WidgetRegistry.register_widget(self._connect_via_url_button, "connect_via_url_button", window_name)

        self._connect_to_simulation_button: ttk.Button = ttk.Button(
            self,
            style=ttk.SUCCESS,
            text=ui_labels.CONNECT_TO_SIMULATION_LABEL,
        )
        WidgetRegistry.register_widget(self._connect_to_simulation_button, "connect_to_simulation_button", window_name)

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

        if show_simulation_button:
            self._connect_to_simulation_button.pack(side=ttk.BOTTOM, fill=ttk.X, padx=sizes.SMALL_PADDING, pady=sizes.MEDIUM_PADDING)

        self._loading_label.pack(side=ttk.TOP, pady=sizes.MEDIUM_PADDING)

    @property
    def loading_text(self) -> str:
        return self._loading_text.get()
    
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
