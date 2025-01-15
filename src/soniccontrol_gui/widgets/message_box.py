import tkinter as tk
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

        self._msg_label = ttk.Label(self, text=self._message)
        self._options_frame = ttk.Frame(self)
        self._option_buttons =  {
            opt.name: ttk.Button(self._options_frame, text=opt.value) for opt in self._dialog_options
        }

        self._msg_label.pack(side="top")
        self._options_frame.pack(side="bottom", pady=10)
        for button in self._option_buttons.values():
            button.pack(side="left", padx=5)

        WidgetRegistry.register_widget(self, self.WIDGET_NAME)
        WidgetRegistry.register_widget(self._msg_label, "message", self.WIDGET_NAME)
        for option in self._dialog_options:
            WidgetRegistry.register_widget(self,option.name, self.WIDGET_NAME)
        
    def destroy(self):
        WidgetRegistry.unregister_widget(self.WIDGET_NAME)
        WidgetRegistry.unregister_widget("message", self.WIDGET_NAME)
        for option in self._dialog_options:
            WidgetRegistry.unregister_widget(option.name, self.WIDGET_NAME)
        super().destroy()

    def add_close_callback(self, callback: Callable[[], None]) -> None:
        self.protocol("WM_DELETE_WINDOW", callback)

    def set_option_buttons_command(self, option: DialogOptions, command: Callable[[], None]) -> None:
        self._option_buttons[option.name].configure(command=command)
    

