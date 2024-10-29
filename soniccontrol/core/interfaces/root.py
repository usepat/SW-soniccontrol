import tkinter as tk
import pathlib
import csv
import asyncio
import logging
import copy
from typing import Iterable, Any, List, Optional, Set, Dict
import ttkbootstrap as ttk
from PIL.ImageTk import PhotoImage
import attrs
from async_tkinter_loop import async_handler
from async_tkinter_loop.mixins import AsyncTk
from tkinter import messagebox
import platform
import subprocess
import time

import soniccontrol.core.interfaces as interfaces
import soniccontrol.constants as const
from soniccontrol.core.interfaces.gui_interfaces import (
    Disconnectable,
    Connectable,
    Scriptable,
    Flashable,
    Updatable,
    RootStringVar,
)
from soniccontrol.core.interfaces.layouts import Layout
from soniccontrol.sonicpackage.sonicamp import SonicAmp, Status, SerialCommunicator

logger = logging.getLogger(__name__)


class Root(tk.Tk, AsyncTk, interfaces.Resizable):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._layouts: Iterable[Layout] = []
        self.resizer: interfaces.Resizer = interfaces.Resizer(self)

        self.serial: Optional[SerialCommunicator] = None
        self.sonicamp: Optional[SonicAmp] = None

        # IMAGES
        self.start_image: PhotoImage = const.Images.get_image(
            const.Images.PLAY_IMG_WHITE, const.Images.BUTTON_ICON_SIZE
        )
        self.restart_image: PhotoImage = const.Images.get_image(
            const.Images.REFRESH_IMG_GREY, const.Images.BUTTON_ICON_SIZE
        )
        self.pause_image: PhotoImage = const.Images.get_image(
            const.Images.PAUSE_IMG_WHITE, const.Images.BUTTON_ICON_SIZE
        )
        self.menue_image: PhotoImage = const.Images.get_image(
            const.Images.MENUE_IMG_WHITE, const.Images.BUTTON_ICON_SIZE
        )
        self.back_image: PhotoImage = const.Images.get_image(
            const.Images.BACK_IMG_WHITE, const.Images.BUTTON_ICON_SIZE
        )
        self.forward_image: PhotoImage = const.Images.get_image(
            const.Images.FORWARDS_IMG_WHITE, const.Images.BUTTON_ICON_SIZE
        )
        self.info_image_small_white: PhotoImage = const.Images.get_image(
            const.Images.INFO_IMG_WHITE, const.Images.BUTTON_ICON_SIZE
        )
        self.connection_image: PhotoImage = const.Images.get_image(
            const.Images.CONNECTION_IMG_WHITE, const.Images.BUTTON_ICON_SIZE
        )
        self.signal_image: PhotoImage = const.Images.get_image(
            const.Images.LIGHTNING_IMG_WHITE, const.Images.BUTTON_ICON_SIZE
        )
        self.home_image: PhotoImage = const.Images.get_image(
            const.Images.HOME_IMG_BLACK, const.Images.TAB_ICON_SIZE
        )
        self.script_image: PhotoImage = const.Images.get_image(
            const.Images.SCRIPT_IMG_BLACK, const.Images.TAB_ICON_SIZE
        )
        self.connection_image: PhotoImage = const.Images.get_image(
            const.Images.CONNECTION_IMG_BLACK, const.Images.TAB_ICON_SIZE
        )
        self.settings_image: PhotoImage = const.Images.get_image(
            const.Images.SETTINGS_IMG_BLACK, const.Images.TAB_ICON_SIZE
        )
        self.info_image: PhotoImage = const.Images.get_image(
            const.Images.INFO_IMG_BLACK, const.Images.TAB_ICON_SIZE
        )
        self.graph_image: PhotoImage = const.Images.get_image(
            const.Images.LINECHART_IMG_BLACK, const.Images.TAB_ICON_SIZE
        )
        self.console_image: PhotoImage = const.Images.get_image(
            const.Images.CONSOLE_IMG_BLACK, (30, 30)
        )
        self.status_image: PhotoImage = const.Images.get_image(
            const.Images.STATUS_IMG_BLACK, const.Images.TAB_ICON_SIZE
        )
        self.signal_off_image: PhotoImage = const.Images.get_image(
            const.Images.LED_RED_IMG,
            (25, 25),
        )
        self.signal_on_image: PhotoImage = const.Images.get_image(
            const.Images.LED_GREEN_IMG, (25, 25)
        )
        self.connection_image_white: PhotoImage = const.Images.get_image(
            const.Images.CONNECTION_IMG_WHITE, const.Images.BUTTON_ICON_SIZE
        )
        self.signal_image_white: PhotoImage = const.Images.get_image(
            const.Images.LIGHTNING_IMG_WHITE, const.Images.BUTTON_ICON_SIZE
        )

        self.firmware_flash_file: pathlib.Path = pathlib.Path()
        self.firmware_flash_file_var: ttk.StringVar = ttk.StringVar(value="")
        self.firmware_flash_file_var.trace_add(
            "write",
            lambda var, index, mode: self._file_path_specified(
                self.firmware_flash_file_var, self.firmware_flash_file
            ),
        )

        self.sonicmeasure_running: asyncio.Event = asyncio.Event()
        self.sonicmeasure_log_var: ttk.StringVar = ttk.StringVar(
            value="logs//sonicmeasure.csv"
        )
        self.sonicmeasure_logfile: pathlib.Path = pathlib.Path(
            self.sonicmeasure_log_var.get()
        )
        self.sonicmeasure_log_var.trace_add(
            "write",
            lambda var, index, mode: self._file_path_specified(
                self.sonicmeasure_log_var, self.sonicmeasure_logfile
            ),
        )

        self.status_log_filepath: pathlib.Path = pathlib.Path("logs//status_log.csv")
        self.status_log_filepath_existed: bool = self.status_log_filepath.exists()
        self.status_log_filepath.parent.mkdir(parents=True, exist_ok=True)
        self.fieldnames: List[str] = [
            "timestamp",
            "signal",
            "frequency",
            "gain",
            "urms",
            "irms",
            "phase",
            "temperature",
        ]

        self.set_frequency_var: ttk.IntVar = ttk.IntVar()
        self.set_gain_var: ttk.IntVar = ttk.IntVar()
        self.wipe_inf_or_def: ttk.BooleanVar = ttk.BooleanVar()
        self.wipe_cycles: ttk.IntVar = ttk.IntVar()

        self.atf_configuration_name: ttk.StringVar = ttk.StringVar(value="None")
        self.atf1: ttk.IntVar = ttk.IntVar(value=0)
        self.atk1: ttk.DoubleVar = ttk.DoubleVar(value=0)
        self.atf2: ttk.IntVar = ttk.IntVar(value=0)
        self.atk2: ttk.DoubleVar = ttk.DoubleVar(value=0)
        self.atf3: ttk.IntVar = ttk.IntVar(value=0)
        self.atk3: ttk.DoubleVar = ttk.DoubleVar(value=0)
        self.att1: ttk.DoubleVar = ttk.DoubleVar(value=0)

        self.status_frequency_khz_var: ttk.DoubleVar = ttk.DoubleVar(value=1000)
        self.status_frequency_text_var: ttk.StringVar = ttk.StringVar()
        self.status_frequency_khz_var.trace_add(
            "write",
            lambda var, index, mode: (
                self.status_frequency_text_var.set(
                    f"Freq.: {self.status_frequency_khz_var.get()/1000} kHz"
                )
            ),
        )

        self.status_gain: ttk.IntVar = ttk.IntVar(value=100)
        self.status_gain_text: ttk.StringVar = ttk.StringVar()
        self.status_gain.trace_add(
            "write",
            lambda var, index, mode: (
                self.status_gain_text.set(f"Gain: {self.status_gain.get()} %")
            ),
        )

        self.temperature: ttk.DoubleVar = ttk.DoubleVar(value=23.5)
        self.temperature_text: ttk.StringVar = ttk.StringVar()
        self.temperature.trace_add(
            "write",
            lambda var, index, mode: (
                self.temperature_text.set(f"Temp.: {self.temperature.get()} °C")
            ),
        )

        self.urms: ttk.IntVar = ttk.IntVar(value=1003)
        self.urms_text: ttk.StringVar = ttk.StringVar()
        self.urms.trace_add(
            "write",
            lambda var, index, mode: (
                self.urms_text.set(f"Urms: {self.urms.get()} mV")
            ),
        )

        self.irms: ttk.IntVar = ttk.IntVar(value=134)
        self.irms_text: ttk.StringVar = ttk.StringVar()
        self.irms.trace_add(
            "write",
            lambda var, index, mode: (
                self.irms_text.set(f"Irms: {self.irms.get()} mA")
            ),
        )

        self.phase: ttk.IntVar = ttk.IntVar(value=75)
        self.phase_text: ttk.StringVar = ttk.StringVar()
        self.phase.trace_add(
            "write",
            lambda var, index, mode: (
                self.phase_text.set(f"Phase: {self.phase.get()} °")
            ),
        )

        self.signal: ttk.BooleanVar = ttk.BooleanVar(value=False)
        self.signal.trace_add(
            "write",
            lambda var, index, mode: (
                self.temperature_text.set(f"Temp.: {self.temperature.get()} °C")
            ),
        )

        self.wipe_mode: ttk.BooleanVar = ttk.BooleanVar(value=False)
        self.wipe_mode.trace_add(
            "write",
            lambda var, index, mode: (
                self.temperature_text.set(f"Temp.: {self.temperature.get()} °C")
            ),
        )

        self.mode: ttk.StringVar = ttk.StringVar(value="Catch")
        self.soniccontrol_state: RootStringVar = RootStringVar(
            value="Manual", master=self
        )
        self.port: ttk.StringVar = ttk.StringVar()

        self.smart_children: Set[ttk.Frame] = set()
        self.disconnectables: Set[Disconnectable] = set()
        self.connectables: Set[Connectable] = set()
        self.updatables: Set[Updatable] = set()
        self.scriptables: Set[Scriptable] = set()
        self.flashables: Set[Flashable] = set()

        self.old_status: Status = Status()
        self.should_update: asyncio.Event = asyncio.Event()
        self.status_condition: asyncio.Condition = asyncio.Condition()
        self.on_status_update_lookup_table: Dict[str, str] = {
            "frequency": "on_frequency_change",
            "gain": "on_gain_change",
            "temperature": "on_temperature_change",
            "signal": "on_signal_change",
            "wipe_mode": "on_wipe_mode_change",
            "protocol": "on_protocol_change",
            "relay_mode": "on_relay_mode_change",
        }

    @property
    def layouts(self) -> Iterable[Layout]:
        return self._layouts

    def set_layouts(self, layouts: Iterable[Layout]) -> None:
        self._layouts = layouts
        self.resizer = interfaces.Resizer(self)

    def add_rootchild(self, rootchild: ttk.Frame) -> ttk.Frame:
        self.smart_children.add(rootchild)
        self.scan_child(rootchild)
        return rootchild

    def scan_child(self, child: ttk.Frame) -> None:
        if isinstance(child, Disconnectable):
            self.disconnectables.add(child)
        if isinstance(child, Connectable):
            self.connectables.add(child)
        if isinstance(child, Updatable):
            self.updatables.add(child)
        if isinstance(child, Scriptable):
            self.scriptables.add(child)
        if isinstance(child, Flashable):
            self.flashables.add(child)

    def bind_events(self) -> None:
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind(const.Events.RESIZING, self.on_resizing)
        self.bind(const.Events.FIRMWARE_FLASH, self.on_firmware_flash)
        self.bind(const.Events.DISCONNECTED, self.on_disconnect)
        self.bind(const.Events.SCRIPT_START, self.on_script_start)
        self.bind(const.Events.SCRIPT_STOP, self.on_script_stop)

    def on_resizing(self, event: Any, *args, **kwargs) -> None:
        return self.resizer.resize(event=event, *args, **kwargs)
    
    def reinitialize(self) -> None:
        messagebox.showinfo("Application Restart", "Flashing succeeded, restart soniccontrol")
    
        # Close the application
        self.destroy()

    def on_firmware_flash(self, event=None) -> None:
        asyncio.create_task(self._async_on_firmware_flash(event))

    async def _async_on_firmware_flash(self, event=None) -> None:
        logger.debug("Close serial connection")
        port: str = self.serial.port
        await self.serial.await_writer_closed()
        
        try:
            print(platform.system())
            if platform.system() == "Linux":
                command = f'"avrdude/Linux/avrdude" -v -p atmega328p -c arduino -P {port} -b 115200 -D -U flash:w:"{self.firmware_flash_file}":i'
            elif platform.system() == "Windows":
                command = f'"avrdude/Windows/avrdude.exe" -v -p atmega328p -c arduino -P {port} -b 115200 -D -U flash:w:"{self.firmware_flash_file}":i'
            
            msgbox = messagebox.showwarning(
                "Process about to start",
                "The program is about to flash a new firmware on your device, please do NOT disconnect or turn off your device during that process",
            )
            
            if msgbox:
                try:
                    result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
                    logger.info(f"Command output: {result.stdout}")
                    self.reinitialize()
                except subprocess.CalledProcessError as e:
                    logger.error(f"Command '{command}' failed with error: {e.stderr}")
                except Exception as e:
                    logger.error(f"An unexpected error occurred: {e}")
                
            else:
                messagebox.showerror("Error", "Cancled the update")
        except WindowsError:
            messagebox.showerror(
                "Error",
                "Something went wrong, please try again. Maybe restart the device and the program",
            )

    def on_disconnect(self) -> None:
        pass

    def on_script_start(self) -> None:
        self.should_update.clear()
        for child in self.updatables:
            self.soniccontrol_state.animate_dots("Script running")
            if hasattr(child, "on_script_start"):
                getattr(child, "on_script_start")()

    def on_script_stop(self) -> None:
        self.should_update.set()
        for child in self.updatables:
            self.soniccontrol_state.stop_animation_of_dots()
            self.soniccontrol_state.set("Manual")
            if hasattr(child, "on_script_stop"):
                getattr(child, "on_script_stop")()

    def on_closing(self) -> None:
        self.sonicamp.disconnect() if self.sonicamp else None
        self.destroy()

    @async_handler
    async def on_connection_attempt(self, event: Any = None, *args, **kwargs) -> None:
        self.serial = SerialCommunicator(self.port.get())
        await self.serial.setup()
        self.sonicamp = await SonicAmp.build_amp(serial=self.serial)
        self.after_connect()
        self.status_engine()

    def after_connect(self) -> None:
        ...

    @async_handler
    async def status_engine(self) -> None:
        async def status_engine_setup() -> None:
            self.serialize_data(
                status=self.sonicamp.status,
                path=self.status_log_filepath,
                first_time=self.status_log_filepath_existed,
            )
            asyncio.create_task(self.update_engine())

        async def worker() -> None:
            while self.sonicamp.serial.connection_open.is_set():
                await self.sonicamp.status_changed.wait()
                self.status_frequency_khz_var.set(self.sonicamp.status.frequency)
                self.status_gain.set(self.sonicamp.status.gain)
                self.temperature.set(self.sonicamp.status.temperature)
                self.urms.set(self.sonicamp.status.urms)
                self.irms.set(self.sonicamp.status.irms)
                self.phase.set(self.sonicamp.status.phase)
                self.on_update()
                self.serialize_data(self.sonicamp.status, self.status_log_filepath)
                await asyncio.sleep(0.1)

        self.should_update.set()
        await status_engine_setup()
        logger.debug("Waiting for change in status")
        status_task = asyncio.create_task(worker())
        await self.sonicamp.serial.connection_closed.wait()
        self.should_update.clear()
        self.event_generate(const.Events.DISCONNECTED)

    async def update_engine(self) -> None:
        while self.sonicamp.serial.connection_open.is_set():
            await self.should_update.wait()
            await self.sonicamp.get_status()
            await asyncio.sleep(0.2)
            if self.sonicamp.status.signal:
                await self.sonicamp.get_sens()
            await asyncio.sleep(0.2)

    def on_update(self) -> None:
        if self.old_status is None:
            self.old_status = copy.deepcopy(self.sonicamp.status)
            return
        for child in self.updatables:
            methods_for_changed_values = (
                getattr(child, method)
                for attribute, method in self.on_status_update_lookup_table.items()
                if (
                    getattr(self.old_status, attribute)
                    != getattr(self.sonicamp.status, attribute)
                )
                and hasattr(child, method)
            )
            for method in methods_for_changed_values:
                logger.debug(f"Calling method {method}")
                method()

        self.old_status = copy.deepcopy(self.sonicamp.status)

    def stop_status_engine(self) -> None:
        if self.sonicamp is not None:
            self.sonicamp.disconnect()
            self.sonicamp = None

    def serialize_data(
        self, status: Status, path: pathlib.Path, first_time: bool = False
    ) -> None:
        is_empty: bool = not path.exists() or path.stat().st_size == 0
        with path.open(mode="a+", newline="") as file:
            writer = csv.DictWriter(
                file, fieldnames=self.fieldnames, extrasaction="ignore"
            )
            if is_empty:
                writer.writeheader()
            writer.writerow(attrs.asdict(self.sonicamp.status))

    def _on_variable_update(
        self, child: Any, method_name: str, *args, **kwargs
    ) -> None:
        if hasattr(child, method_name):
            getattr(child, method_name)(*args, **kwargs)

    def _file_path_specified(
        self, var: ttk.StringVar, path: pathlib.Path, *args, **kwargs
    ) -> None:
        path = pathlib.Path(var.get())
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
