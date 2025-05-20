import tkinter as tk
from tkinter import font
from typing import Callable, List
import ttkbootstrap as ttk
from enum import Enum
import asyncio

from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import View


class DialogOptions(Enum):
    CLOSE = "Close"
    CANCEL = "Cancel"
    YES = "Yes"
    NO = "No"
    OK = "Ok"
    PROCEED = "Proceed"

class MessageBox(UIComponent):
    def __init__(self, root, message: str, title: str, options: List[DialogOptions]):
        self._options: List[DialogOptions] = options
        self._view = MessageBoxView(root,message, title, self._options)
        self._answer = asyncio.Future()
        super().__init__(None, self._view)
        
        for opt in self._options:
            def clicked_callback(option=opt): # we need to pass opt as keyword argument, to capture it by value and not by reference
                self._answer.set_result(option)
                self._view.destroy()

            self._view.set_option_buttons_command(opt, clicked_callback)

        def close_message_box_callback():
            if not self._answer.done():
                self._answer.set_result(None)
        self._view.add_close_callback(close_message_box_callback)


    async def wait_for_answer(self) -> DialogOptions | None:
        return await self._answer

    @staticmethod
    def show_error(root, message: str, title: str = "Error") -> "MessageBox":
        return MessageBox(root, message, title, [DialogOptions.OK])     

    @staticmethod
    def show_ok(root, message: str, title: str = "") -> "MessageBox":
        return MessageBox(root, message, title, [DialogOptions.OK])

    @staticmethod
    def show_ok_cancel(root, message: str, title: str = "") -> "MessageBox":
        return MessageBox(root, message, title, [DialogOptions.OK, DialogOptions.CANCEL])

    @staticmethod
    def show_yes_no(root, message: str, title: str = "") -> "MessageBox":
        return MessageBox(root, message, title, [DialogOptions.YES, DialogOptions.NO])


class MessageBoxView(tk.Toplevel, View):
    WIDGET_NAME = "MessageBox"

    def __init__(self, root, message: str, title: str, dialog_options: List[DialogOptions], *args, **kwargs):
        super().__init__(root, *args, **kwargs)
        self.title(title)

        self._message = message
        self._dialog_options = dialog_options
        self._close_callback: Callable[[], None] = lambda: None
        # Check if the text contains an even number of ** for formatting bold text. We could use regex here and in general create a better method for formatting text.
        # But it works, so I dont care right now
        if message.count("**") % 2 == 0 and message.count("**") != 0:
            self._msg_label = tk.Text(self,
                wrap="word",               # soft-wrap on words
                height=1,                  # will auto-grow later
                borderwidth=0,             # no relief
                highlightthickness=0,      # no focus ring
                background=self.cget("background"),
                relief="flat",
            )
            self.create_bold_text()
        else:
            self._msg_label = ttk.Label(self, text=self._message)
        self._options_frame = ttk.Frame(self)
        self._option_buttons =  {
            opt: ttk.Button(self._options_frame, text=opt.value) for opt in self._dialog_options
        }

        self._msg_label.pack(side="top")
        self._options_frame.pack(side="bottom", pady=10)
        for button in self._option_buttons.values():
            button.pack(side="left", padx=5)

        WidgetRegistry.register_widget(self, self.WIDGET_NAME)
        WidgetRegistry.register_widget(self._msg_label, "message", self.WIDGET_NAME)
        for option in self._dialog_options:
            WidgetRegistry.register_widget(self._option_buttons[option],option.name, self.WIDGET_NAME)

    def create_bold_text(self,
                     max_chars: int = 60,      # ≈ dialog width
                     max_lines: int = 12):     # vertical ceiling
        assert isinstance(self._msg_label, ttk.Text)
        txt = self._msg_label
        txt.configure(state="normal",
                    wrap="word",
                    borderwidth=0,
                    highlightthickness=0,
                    relief="flat",
                    width=max_chars)             # 1️⃣  limit width

        # --- insert bold / normal text exactly as before -----------------
        bold_font = font.nametofont("TkDefaultFont").copy()
        bold_font.configure(weight="bold")
        txt.tag_configure("bold", font=bold_font)

        for i, chunk in enumerate(self._message.split("**")):
            tag = "bold" if i % 2 else ()
            txt.insert("end", chunk, tag)
        # -----------------------------------------------------------------

        txt.update_idletasks()                     # make geometry info valid
        lines = txt.count("1.0", "end-1c", "displaylines")[0]

        txt.configure(
            height=min(lines / max_chars, max_lines),          # 2️⃣  grow just enough
            state="disabled",                      # 3️⃣  lock the widget
        )

        
    def destroy(self):
        WidgetRegistry.unregister_widget(self.WIDGET_NAME)
        WidgetRegistry.unregister_widget("message", self.WIDGET_NAME)
        for option in self._dialog_options:
            WidgetRegistry.unregister_widget(option.name, self.WIDGET_NAME)
        super().destroy()
        self._close_callback()

    def add_close_callback(self, callback: Callable[[], None]) -> None:
        self._close_callback = callback

    def set_option_buttons_command(self, option: DialogOptions, command: Callable[[], None]) -> None:
        self._option_buttons[option].configure(command=command)
    

