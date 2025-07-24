
import asyncio
from enum import Enum
import logging
from pathlib import Path
from typing import Final, Callable
from soniccontrol.updater import Updater
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.view import TabView
from soniccontrol.flashing.firmware_flasher import NewFirmwareFlasher, LegacyFirmwareFlasher
from soniccontrol.sonic_device import SonicDevice

from async_tkinter_loop import async_handler

import ttkbootstrap as ttk

from soniccontrol_gui.constants import sizes, ui_labels
from soniccontrol.events import Event, PropertyChangeEvent
from soniccontrol_gui.views.core.app_state import AppState
from soniccontrol_gui.resources import images
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.widgets.file_browse_button import FileBrowseButtonView


# List of all flash mode options
class FLASH_OPTIONS(Enum):
    FLASH_USB = ui_labels.FLASH_USB
    FLASH_UART_SLOW = ui_labels.FLASH_UART_SLOW 
    FLASH_UART_FAST = ui_labels.FLASH_UART_FAST
    FLASH_LEGACY = ui_labels.FLASH_LEGACY


class Flashing(UIComponent):
    RECONNECT_EVENT = "Reconnect"
    FAILED_EVENT = "Flashing failed"
    def __init__(self, parent: UIComponent, logger: logging.Logger, app_state: AppState, updater: Updater , port: str, device: SonicDevice):
        self._port = port
        self._updater = updater
        self._app_state = app_state
        self._device = device
        self._view = FlashingView(parent.view)
        super().__init__(self, self._view)
        self._logger = logging.getLogger(logger.name + "." + Flashing.__name__)
        if self._app_state:
            self._app_state.subscribe_property_listener(AppState.EXECUTION_STATE_PROP_NAME, self._on_execution_state_changed)

        self._view.set_submit_button_command(self._flash)

    @async_handler
    async def _flash(self) -> None:
        selected_file = self._view.get_selected_file_path()
        if selected_file is None:
            self._logger.info(f"No file for flashing selected")
            return
        flasher = LegacyFirmwareFlasher(serial_port=self._port, filepath=selected_file)

    
        if self._updater:
            await self._updater.stop()
            self._logger.info("Stopped Updater")
        await self._device.disconnect()
        success = await flasher.flash_firmware()
        if success:
            self.emit(Event(Flashing.RECONNECT_EVENT))
        else:
            self.emit(Event(Flashing.FAILED_EVENT))

    def _on_execution_state_changed(self, e: PropertyChangeEvent) -> None:
        pass

class FlashingView(TabView):
    def __init__(self, master: ttk.Frame, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

    @property
    def image(self) -> ttk.ImageTk.PhotoImage:
        return ImageLoader.load_image_resource(images.SETTINGS_ICON_BLACK, sizes.TAB_ICON_SIZE)

    @property
    def tab_title(self) -> str:
        return ui_labels.FLASHER_LABEL
    
    def _initialize_children(self) -> None:
        widget_name = "Flashing"

        FLASH_PADDING: Final[tuple[int, int, int, int]] = (5, 0, 5, 5)
        self._flash_frame: ttk.Labelframe = ttk.Labelframe(
            self, padding=FLASH_PADDING
        )

        self._browse_flash_file_button: FileBrowseButtonView = FileBrowseButtonView(
            self._flash_frame, widget_name, text=ui_labels.SPECIFY_PATH_LABEL
        )
        self._submit_button: ttk.Button = ttk.Button(
            self._flash_frame, text=ui_labels.SUBMIT_LABEL, style=ttk.DARK
        )

    def _initialize_publish(self) -> None:
        self._flash_frame.pack(expand=True, fill=ttk.BOTH)
        self._flash_frame.columnconfigure(0, weight=sizes.EXPAND)
        self._flash_frame.rowconfigure(0, weight=sizes.DONT_EXPAND)
        self._flash_frame.rowconfigure(1, weight=sizes.DONT_EXPAND)

        self._browse_flash_file_button.grid(
            row=1,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.EW,
        )
        self._submit_button.grid(
            row=2,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.EW,
        )

    def set_submit_button_command(self, command: Callable[[], None]) -> None:
        self._submit_button.configure(command=command)
    
    def get_selected_file_path(self) -> Path | None:
        """Retrieve the file path from the file browse button."""
        return self._browse_flash_file_button.path


async def main():
    logger = logging.getLogger("Flashing")
    selected_file = Path(r"\\wsl.localhost\Ubuntu\home\usepat\GitHub\FW-sonic-firmware\build\pico\mvp_worker_v2_5_1_with_bootloader\devices\firmware_main.elf")
    flasher = NewFirmwareFlasher(logger, 115200, selected_file, 0.1)
    success = await flasher.flash_firmware()
    print("Flashing successful" if success else "Flashing failed")





if __name__ == "__main__":
    asyncio.run(main())