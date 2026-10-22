import asyncio
import tkinter as tk
from collections.abc import Callable
from enum import Enum
from math import ceil
from tkinter import font

import ttkbootstrap as ttk

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
    def __init__(self, root, message: str, title: str, options: list[DialogOptions]):
        self._options: list[DialogOptions] = options
        self._view = MessageBoxView(root, message, title, self._options)
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
    WRAP_LENGTH_PX = 420
    MIN_TEXT_WIDTH_CHARS = 20

    def __init__(self, root, message: str, title: str, dialog_options: list[DialogOptions], *args, **kwargs):
        super().__init__(root, *args, **kwargs)
        self.title(title)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self._message = message
        self._dialog_options = dialog_options
        self._close_callback: Callable[[], None] = lambda: None
        self._root = root
        self._main_frame = ttk.Frame(self, padding=(12, 12, 12, 10))
        self._main_frame.pack(fill=tk.BOTH)
        self._message_widget: tk.Widget
        if self._uses_rich_text():
            self._message_widget = tk.Text(
                self._main_frame,
                wrap="word",
                height=1,
                borderwidth=0,
                highlightthickness=0,
                background=self.cget("background"),
                relief="flat",
                padx=0,
                pady=0,
                spacing1=0,
                spacing2=0,
                spacing3=0,
            )
        else:
            self._message_widget = ttk.Label(
                self._main_frame,
                text=self._message,
                justify=tk.LEFT,
                wraplength=self.WRAP_LENGTH_PX,
                anchor=tk.W,
            )

        self._options_frame = ttk.Frame(self._main_frame)
        self._option_buttons =  {
            opt: ttk.Button(self._options_frame, text=opt.value) for opt in self._dialog_options
        }

        self._message_widget.pack(side="top", fill="x", anchor=tk.W, pady=(0, 8))
        self._options_frame.pack(side="top", anchor=tk.CENTER)
        for button in self._option_buttons.values():
            button.pack(side="left", padx=5)

        self.resizable(False, False)
        self.after_idle(self._finalize_layout)

        WidgetRegistry.register_widget(self, self.WIDGET_NAME)
        WidgetRegistry.register_widget(self._message_widget, "message", self.WIDGET_NAME)
        for option in self._dialog_options:
            WidgetRegistry.register_widget(self._option_buttons[option],option.name, self.WIDGET_NAME)

    def _finalize_layout(self) -> None:
        self.deiconify()
        if self._uses_rich_text():
            self._create_bold_text()
        self._fit_to_content()
        self._center_window()
        self.focus_set()
        self.grab_set()

    def _fit_to_content(self) -> None:
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        self.geometry(f"{width}x{height}")
        self.minsize(width, height)
        self.maxsize(width, height)

    def _center_window(self) -> None:
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()

        parent = self._root.winfo_toplevel()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        x = parent_x + max(0, (parent_width - width) // 2)
        y = parent_y + max(0, (parent_height - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _uses_rich_text(self) -> bool:
        return self._message.count("**") % 2 == 0 and self._message.count("**") != 0

    def _create_bold_text(
        self,
        max_lines: int = 12,
    ):
        assert isinstance(self._message_widget, tk.Text)
        txt = self._message_widget
        txt.delete("1.0", "end")
        default_font = font.nametofont("TkDefaultFont")
        average_char_width = max(1, default_font.measure("abcdefghijklmnopqrstuvwxyz") // 26)
        text_width_chars = max(self.MIN_TEXT_WIDTH_CHARS, ceil(self.WRAP_LENGTH_PX / average_char_width))
        txt.configure(
            state="normal",
            wrap="word",
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
            width=text_width_chars,
        )

        # --- insert bold / normal text exactly as before -----------------
        bold_font = default_font.copy()
        bold_font.configure(weight="bold")
        txt.tag_configure("bold", font=bold_font)

        if self._uses_rich_text():
                    # Check if the text contains an even number of ** for formatting bold text. We could use regex here and in general create a better method for formatting text.
                    # But it works, so I dont care right now
            for i, chunk in enumerate(self._message.split("**")):
                tag = "bold" if i % 2 else ()
                txt.insert("end", chunk, tag)
        else:
            txt.insert("end", self._message)
        # -----------------------------------------------------------------

        visible_lines = max(1, min(self._estimate_visible_lines(default_font), max_lines))
        txt.configure(
            height=visible_lines,
            state="disabled",
        )
        txt.update_idletasks()

    def _estimate_visible_lines(self, base_font: font.Font) -> int:
        plain_message = self._message.replace("**", "")
        line_count = 0

        for paragraph in plain_message.splitlines() or [plain_message]:
            if not paragraph:
                line_count += 1
                continue

            current_width = 0
            paragraph_lines = 1
            for word in paragraph.split():
                word_width = base_font.measure(f"{word} ")
                if current_width and current_width + word_width > self.WRAP_LENGTH_PX:
                    paragraph_lines += 1
                    current_width = word_width
                else:
                    current_width += word_width

            line_count += paragraph_lines

        return line_count

        
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
    

