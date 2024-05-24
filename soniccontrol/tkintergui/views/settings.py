from typing import Final

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame, ScrolledText

from soniccontrol.interfaces.view import TabView
from soniccontrol.tkintergui.utils.constants import sizes, ui_labels
from soniccontrol.tkintergui.utils.image_loader import ImageLoader
from soniccontrol.utils.files import images


class ATK_Frame(ttk.Frame):
    def __init__(self, master: ttk.tk.Widget, label: str, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)
        self._label: ttk.Label = ttk.Label(self, text=label)
        self._spinbox: ttk.Spinbox = ttk.Spinbox(self)

    def bind_variable(self, variable: ttk.Variable) -> None:
        self._spinbox.configure(textvariable=variable)

    def publish(self) -> None:
        self.columnconfigure(0, weight=sizes.EXPAND)
        self.columnconfigure(1, weight=sizes.EXPAND)
        self.rowconfigure(0, weight=sizes.EXPAND)
        self._label.grid(
            row=0,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.E,
        )
        self._spinbox.grid(
            row=0,
            column=1,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.W,
        )


class SettingsView(TabView):
    def __init__(self, master: ttk.Window, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    @property
    def image(self) -> ttk.ImageTk.PhotoImage:
        return ImageLoader.load_image(images.SETTINGS_ICON_BLACK, sizes.TAB_ICON_SIZE)

    @property
    def tab_title(self) -> str:
        return ui_labels.SETTINGS_LABEL

    def _initialize_children(self) -> None:
        self._main_frame: ttk.Frame = ttk.Frame(self)
        self._notebook: ttk.Notebook = ttk.Notebook(self._main_frame)

        FLASH_PADDING: Final[tuple[int, int, int, int]] = (5, 0, 5, 5)
        self._flash_settings_frame: ttk.Frame = ttk.Frame(self._main_frame)
        self._flash_frame: ttk.Labelframe = ttk.Labelframe(
            self._flash_settings_frame, padding=FLASH_PADDING
        )
        self._file_entry: ttk.Entry = ttk.Entry(self._flash_frame)
        self._browse_files_button: ttk.Button = ttk.Button(
            self._flash_frame, text=ui_labels.SPECIFY_PATH_LABEL, style=ttk.DARK
        )
        self._submit_button: ttk.Button = ttk.Button(
            self._flash_frame, text=ui_labels.SUBMIT_LABEL, style=ttk.DARK
        )

        self._sonicamp_settings_frame: ttk.Frame = ttk.Frame(self._main_frame)
        self._new_config_button: ttk.Button = ttk.Button(
            self._sonicamp_settings_frame,
            text=ui_labels.NEW_LABEL,
            style=ttk.DARK,
            # image=utils.ImageLoader.load_image(
            #     images.PLUS_ICON_WHITE, sizes.BUTTON_ICON_SIZE
            # ),
        )
        self._config_entry: ttk.Combobox = ttk.Combobox(
            self._sonicamp_settings_frame, style=ttk.DARK
        )
        self._save_config_button: ttk.Button = ttk.Button(
            self._sonicamp_settings_frame, text=ui_labels.SAVE_LABEL, style=ttk.DARK
        )
        self._send_config_button: ttk.Button = ttk.Button(
            self._sonicamp_settings_frame, text=ui_labels.SEND_LABEL, style=ttk.SUCCESS
        )
        self._progress_bar: ttk.Progressbar = ttk.Progressbar(
            self._sonicamp_settings_frame, orient=ttk.HORIZONTAL, style=ttk.SUCCESS
        )
        self._parameters_frame: ScrolledFrame = ScrolledFrame(
            self._sonicamp_settings_frame, autohide=True
        )
        self._atf1_frame: ATK_Frame = ATK_Frame(self._parameters_frame, ui_labels.ATF1)
        self._atf2_frame: ATK_Frame = ATK_Frame(self._parameters_frame, ui_labels.ATF2)
        self._atf3_frame: ATK_Frame = ATK_Frame(self._parameters_frame, ui_labels.ATF3)
        self._atk1_frame: ATK_Frame = ATK_Frame(self._parameters_frame, ui_labels.ATK1)
        self._atk2_frame: ATK_Frame = ATK_Frame(self._parameters_frame, ui_labels.ATK2)
        self._atk3_frame: ATK_Frame = ATK_Frame(self._parameters_frame, ui_labels.ATK3)
        self._att1_frame: ATK_Frame = ATK_Frame(self._parameters_frame, ui_labels.ATT1)
        self._commandset_labelframe: ttk.Labelframe = ttk.Labelframe(
            self._parameters_frame, text=ui_labels.COMMAND_SET
        )
        self._commandset_frame: ScrolledText = ScrolledText(
            self._commandset_labelframe, autohide=True
        )

    def _initialize_publish(self) -> None:
        self._main_frame.pack(expand=True, fill=ttk.BOTH)
        self._notebook.pack(expand=True, fill=ttk.BOTH)
        self._notebook.add(
            self._flash_settings_frame, text=ui_labels.FLASH_SETTINGS_LABEL
        )
        self._notebook.add(
            self._sonicamp_settings_frame, text=ui_labels.SONICAMP_SETTINGS_LABEL
        )

        self._flash_frame.pack(expand=True)
        self._flash_frame.columnconfigure(0, weight=sizes.EXPAND)
        self._flash_frame.columnconfigure(1, weight=sizes.DONT_EXPAND)
        self._flash_frame.rowconfigure(0, weight=sizes.DONT_EXPAND)
        self._flash_frame.rowconfigure(1, weight=sizes.DONT_EXPAND)
        self._file_entry.grid(
            row=0,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.EW,
        )
        self._browse_files_button.grid(
            row=0,
            column=1,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )
        self._submit_button.grid(
            row=1,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.EW,
            columnspan=2,
        )

        self._sonicamp_settings_frame.columnconfigure(0, weight=sizes.DONT_EXPAND)
        self._sonicamp_settings_frame.columnconfigure(1, weight=sizes.EXPAND)
        self._sonicamp_settings_frame.columnconfigure(2, weight=sizes.DONT_EXPAND)
        self._sonicamp_settings_frame.columnconfigure(3, weight=sizes.DONT_EXPAND)
        self._sonicamp_settings_frame.rowconfigure(2, weight=sizes.EXPAND)
        self._new_config_button.grid(
            row=0,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )
        self._config_entry.grid(
            row=0,
            column=1,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.EW,
        )
        self._save_config_button.grid(
            row=0,
            column=2,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )
        self._send_config_button.grid(
            row=0,
            column=3,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )
        self._progress_bar.grid(
            row=1,
            column=0,
            columnspan=4,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.EW,
        )
        self._parameters_frame.grid(
            row=2,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            columnspan=4,
            sticky=ttk.NSEW,
        )
        self._parameters_frame.columnconfigure(0, weight=sizes.EXPAND)
        self._atf1_frame.grid(
            row=0,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.EW,
        )
        self._atk1_frame.grid(
            row=1,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.EW,
        )
        self._atf2_frame.grid(
            row=2,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.EW,
        )
        self._atk2_frame.grid(
            row=3,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.EW,
        )
        self._atf3_frame.grid(
            row=4,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.EW,
        )
        self._atk3_frame.grid(
            row=5,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.EW,
        )
        self._att1_frame.grid(
            row=6,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.EW,
        )
        for child in self._parameters_frame.winfo_children():
            if hasattr(child, "publish"):
                child.publish()
        self._commandset_labelframe.grid(
            row=7,
            column=0,
            padx=sizes.SIDE_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )
        self._commandset_frame.pack(
            expand=True,
            fill=ttk.BOTH,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )

    def publish(self) -> None:
        ...