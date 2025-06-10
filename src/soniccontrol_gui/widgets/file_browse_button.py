from pathlib import Path
from tkinter import filedialog
from typing import Any, Optional
import ttkbootstrap as ttk

from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import View


class FileBrowseButtonView(View):
    def __init__(self, master: Any, parent_widget_name: str, *args, **kwargs):
        self._parent_widget_name = parent_widget_name
        self._text = kwargs.pop("text", "")
        self._default_extension = kwargs.pop("default_extension", None)
        self._filetypes = kwargs.pop("filetypes", None)
        super().__init__(master, *args, **kwargs)
        
    def _initialize_children(self) -> None:
        self._path_str = ttk.StringVar(self, value="")
        self._frame = ttk.Frame(self)
        self._prefix_text = ttk.Label(self._frame, text=self._text)
        self._path_entry = ttk.Entry(self._frame, textvariable=self._path_str)
        self._button = ttk.Button(self._frame, text="Browse Files", command=self._browse_files)

        WidgetRegistry.register_widget(self._path_entry, "browse_files_entry", self._parent_widget_name)
        WidgetRegistry.register_widget(self._button, "browse_files_button", self._parent_widget_name)

    def _initialize_publish(self) -> None:
        self._frame.pack(expand = True, fill=ttk.BOTH)

        self._frame.columnconfigure(0, weight=0) 
        self._frame.columnconfigure(1, weight=1)
        self._frame.columnconfigure(2, weight=0)

        self._prefix_text.grid(row=0, column=0, padx=(0, 10), pady=10, sticky=ttk.W)
        self._path_entry.grid(row=0, column=1, padx=(0, 10), pady=10, sticky=ttk.EW)
        self._button.grid(row=0, column=2, padx=10, pady=10, sticky=ttk.E)

    @property 
    def path(self) -> Optional[Path]:
        path = self._path_str.get()
        return Path(path) if path != "" else None

    @path.setter
    def path(self, value: Optional[Path]) -> None:
        self._path_str.set("" if value is None else value.as_posix())

    def _browse_files(self) -> None:
        # I do not know why I have to do it this way and cant just pass None for the single keyword args.
        # Danke Merkel.. Sorry, I meant Tkinter
        kwargs = {} 
        if self._default_extension is not None:
            kwargs["defaultextension"] = self._default_extension
        if self._filetypes is not None:
            kwargs["filetypes"] = self._filetypes
        filename: str = filedialog.askopenfilename(**kwargs)

        if filename == "." or filename == "" or isinstance(filename, (tuple)):
            return

        path = Path(filename)
        self._path_str.set(path.as_posix())
