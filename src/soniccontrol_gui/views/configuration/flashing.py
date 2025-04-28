
import asyncio
from enum import Enum
import logging
from pathlib import Path
from typing import Final, Callable
from soniccontrol.updater import Updater
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.view import TabView
from soniccontrol.flashing.firmware_flasher import NewFirmwareFlasher
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
    def __init__(self, parent: UIComponent, logger: logging.Logger, device: SonicDevice, app_state: AppState, updater: Updater | None = None):
        self._writer = device.communicator.writer
        self._reader = device.communicator.reader
        self._communicator = device.communicator

        self._updater = updater
        self._device = device
        self._app_state = app_state
        self._view = FlashingView(parent.view)
        super().__init__(self, self._view)
        self._logger = logging.getLogger(logger.name + "." + Flashing.__name__)
        if self._app_state:
            self._app_state.subscribe_property_listener(AppState.EXECUTION_STATE_PROP_NAME, self._on_execution_state_changed)

        self._view.set_submit_button_command(self._flash)

    @async_handler
    async def _flash(self) -> None:
        selected_flash_mode = self._view.get_selected_flash_mode()
        selected_file = self._view.get_selected_file_path()
        if selected_file is None:
            self._logger.info(f"No file for flashing selected")
            return
        self._logger.info(f"Selected flash option: {selected_flash_mode}")
        flasher = None

        # TODO: consider using match case here
        if selected_flash_mode == ui_labels.FLASH_LEGACY:
            # TODO implement legacy flashing
            self._logger.info("Executed command FLASH_LEGACY")
        elif selected_flash_mode == ui_labels.FLASH_UART_SLOW:
            flasher = NewFirmwareFlasher(self._logger, 9600, selected_file, 0.3)
            self._logger.info("Executed command FLASH_UART_SLOW")
        elif selected_flash_mode == ui_labels.FLASH_UART_FAST:
            flasher = NewFirmwareFlasher(self._logger, 115200, selected_file, 0.5)
            self._logger.info("Executed command FLASH_UART_FAST")
        elif selected_flash_mode == ui_labels.FLASH_USB:
            flasher = NewFirmwareFlasher(self._logger, 115200, selected_file)
            self._logger.info("Executed command FLASH_USB")
        if flasher is None:
            self._logger.info("Flasher was not found")
            return
        command = "!" + selected_flash_mode

        if self._updater:
            await self._updater.stop()
            self._logger.info("Stopped Updater")

        if self._device and isinstance(flasher, NewFirmwareFlasher):
            await self._device.execute_command(command)
            self._logger.info(f"Executed command {command}")
            await self._device.communicator.close_communication(True)
            self._logger.info("Sleep for 10s")
            await asyncio.sleep(10)
            # Read the response (4 bytes)
            # response = await self._reader.read(4)

        success = await flasher.flash_firmware()
        # boot_command = b'BOOT'  # "BOOT" as bytes
        # zero_value = (0).to_bytes(4, byteorder='big')  # 0 as 4-byte big-endian integer  
        # Combine the two parts
        # command = boot_command + zero_value
        # self._writer.write(command)
        # await self._writer.drain()  
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
        FLASH_PADDING: Final[tuple[int, int, int, int]] = (5, 0, 5, 5)
        self._flash_frame: ttk.Labelframe = ttk.Labelframe(
            self, padding=FLASH_PADDING
        )
        #self._baud: ttk.Entry = Entry
        self._flash_mode = ttk.StringVar()
        self._flash_mode_combobox: ttk.Combobox = ttk.Combobox(
            self._flash_frame,
            textvariable=self._flash_mode,
            values=[ opt.value for opt in FLASH_OPTIONS ],  # Use predefined flash options
            state='readonly',
        )
        self._flash_mode_combobox.current(0)  # Set default to the first option


        self._browse_flash_file_button: FileBrowseButtonView = FileBrowseButtonView(
            self._flash_frame, text=ui_labels.SPECIFY_PATH_LABEL
        )
        self._submit_button: ttk.Button = ttk.Button(
            self._flash_frame, text=ui_labels.SUBMIT_LABEL, style=ttk.DARK
        )

    def _initialize_publish(self) -> None:
        self._flash_frame.pack(expand=True, fill=ttk.BOTH)
        self._flash_frame.columnconfigure(0, weight=sizes.EXPAND)
        self._flash_frame.rowconfigure(0, weight=sizes.DONT_EXPAND)
        self._flash_frame.rowconfigure(1, weight=sizes.DONT_EXPAND)

        self._flash_mode_combobox.grid(
            row=0,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.EW,
        )


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

    def get_selected_flash_mode(self) -> str:
        return self._flash_mode.get()  # Retrieve the selected flash mode
    
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