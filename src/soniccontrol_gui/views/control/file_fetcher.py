from pathlib import Path

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
import asyncio
from typing import Callable
from async_tkinter_loop import async_handler
from soniccontrol.data_capturing.files import FileDescription, discover_files, get_file_extension_for_file_type, load_file
from soniccontrol.sonic_device import SonicDevice
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.view import TabView, View
from soniccontrol_gui.resources import images
from soniccontrol_gui.constants import sizes, ui_labels
from soniccontrol_gui.widgets.message_box import MessageBox



class FileEntryView(View):
    def __init__(self, master: ttk.Window,  file_desc: FileDescription, *args, **kwargs) -> None:
        self._file_desc = file_desc
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        self._label_name = ttk.Label(self, text=self._file_desc.name)
        self._label_type = ttk.Label(self, text=self._file_desc.file_type.name.lower())
        self._label_timestamp = ttk.Label(self, text=self._file_desc.time_stamp.isoformat())
        self._label_size = ttk.Label(self, text=str(self._file_desc.file_size))
        self._download_button = ttk.Button(self, text=ui_labels.DOWNLOAD)

    def _initialize_publish(self) -> None:
        self.pack(fill=ttk.X, side=ttk.TOP, pady=sizes.SMALL_PADDING)

        self.grid_columnconfigure(0, weight=1)  
        self.grid_columnconfigure(1, weight=1)  
        self.grid_columnconfigure(2, weight=1)  
        self.grid_columnconfigure(3, weight=1) 
        self.grid_columnconfigure(4, weight=0)

        self._label_name.grid(row=0, column=0, sticky=ttk.EW)  
        self._label_type.grid(row=0, column=1, sticky=ttk.EW)  
        self._label_timestamp.grid(row=0, column=2, sticky=ttk.EW)  
        self._label_size.grid(row=0, column=3, sticky=ttk.EW)  
        self._download_button.grid(row=0, column=4, sticky=ttk.EW)  

    def set_download_file_command(self, command: Callable[[], None]) -> None:
        self._download_button.configure(command=command)



class FileTab(UIComponent):
    def __init__(self, parent: UIComponent, device: SonicDevice):
        self._device = device
        self._view = FileTabView(parent.view)
        super().__init__(parent, self._view)

        self._lock = asyncio.Lock()
        
        self.top_level_window.pass_loading_task(self._load_files())

        self._view.set_load_files_command(async_handler(self._load_files))

    async def _load_files(self):
        async with self._lock:
            # destroy previous entries
            for child in self._view.file_list_slot.children.values():
                child.destroy()

            for f in await discover_files(self._device):
                file_entry = FileEntryView(self._view.file_list_slot, f)
                # I am using here keyword param to capture the variable inside the lambda
                file_entry.set_download_file_command(lambda x=f.file_index: self._download_file(x))

    @async_handler
    async def _download_file(self, file_index: int):
        file_desc, file_data = await load_file(self._device, file_index)

        ext = get_file_extension_for_file_type(file_desc.file_type)
        file_path = Path.home() / "Downloads" / f"{file_index}_{file_desc.name}.{ext}"
        with open(file_path, "wb") as f:
            f.write(file_data)

        MessageBox.show_ok(self.view.root, f"File successfully downloaded to {file_path}")

    
class FileTabView(TabView):
    def __init__(self, master: ttk.Window, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    @property
    def image(self) -> ttk.ImageTk.PhotoImage:
        return ImageLoader.load_image_resource(images.CONSOLE_ICON_BLACK, sizes.TAB_ICON_SIZE)

    @property
    def tab_title(self) -> str:
        return ui_labels.FILES_LABEL
    
    def _initialize_children(self) -> None:
        self._main_frame = ttk.Frame(self)
        self._reload_files_button = ttk.Button(self._main_frame, text=ui_labels.REFRESH)
        self._horizontal_scrolled_frame: ScrolledFrame = ScrolledFrame(
            self._main_frame, autohide=True
        )
        self._file_list_slot = ttk.Frame(self._horizontal_scrolled_frame)

    def _initialize_publish(self) -> None:
        self._main_frame.pack(expand=True, fill=ttk.BOTH)
        self._reload_files_button.pack(fill=ttk.X, padx=sizes.MEDIUM_PADDING, pady=sizes.MEDIUM_PADDING)
        self._horizontal_scrolled_frame.pack(
            expand=True, 
            fill=ttk.BOTH,
            pady=sizes.MEDIUM_PADDING,
            padx=sizes.MEDIUM_PADDING
        )
        self._file_list_slot.pack(
            fill=ttk.X, side=ttk.TOP,
            pady=sizes.MEDIUM_PADDING,
            padx=sizes.MEDIUM_PADDING
        )

    @property
    def file_list_slot(self) -> View:
        return self._file_list_slot #type: ignore

    def set_load_files_command(self, command: Callable[[], None]):
        self._reload_files_button.configure(command=command)
