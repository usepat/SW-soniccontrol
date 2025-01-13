import asyncio
from typing import Dict, Optional
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledText
import datetime

from soniccontrol_gui.view import TabView


def get_text_of_widget(widget: tk.Widget) -> str:
    if isinstance(widget, (tk.Entry, ttk.Entry, ttk.Combobox)):
        return widget.get()
    elif isinstance(widget, ScrolledText):
        return widget.text.get(1.0, ttk.END)
    elif isinstance(widget, (tk.Label, ttk.Label, tk.Button, ttk.Button, ttk.Checkbutton)):
        return str(widget.cget("text"))
    elif isinstance(widget, ttk.Meter):
        return str(widget.amountusedvar.get())
    elif isinstance(widget, (ttk.Notebook)):
        return "" # has no text
    elif widget.__class__.__name__ == "Notebook":
        return "" # has no text
    elif isinstance(widget, TabView):
        return widget.tab_title
    elif widget.__class__.__name__ == "MessageBoxView":
        return widget.title()
    else:
        raise TypeError("The object has to be of type tk.Label, tk.Entry or tk.Button or inherit from them")

def set_text_of_widget(widget: tk.Widget, text: str) -> None:
    if isinstance(widget, (tk.Entry, ttk.Entry)):
        widget.delete(0, ttk.END)
        widget.insert(0, text)
    elif isinstance(widget, ScrolledText):
        widget.text.delete(1.0, ttk.END)
        widget.text.insert(ttk.INSERT, text)
    elif isinstance(widget, ttk.Combobox):
        widget.set(text)
    elif isinstance(widget, ttk.Meter):
        widget.configure(amountused=int(text))
    elif isinstance(widget, (tk.Label, ttk.Label, tk.Button, ttk.Button, ttk.Checkbutton)):
        widget.config(text=text)
    else:
        raise TypeError("The object has to be of type tk.Label, tk.Entry or tk.Button or inherit from them")



class WidgetReference:
    def __init__(self, widget: tk.Widget):
        self.widget: tk.Widget = widget
        self.old_text_value = get_text_of_widget(self.widget)
        self.last_time_text_has_changed = datetime.datetime.now()
        self.text_has_changed = asyncio.Event()

"""!
@brief Registry solely used for robot testing library

The widgets are available in a static directory of this class. 
This would be bad practice for normal code, because we have global state.
However for our robot testing library it is necessary, so that we can access the widgets easily.

You have to enable the registry with @ref WidgetRegistry.set_up, 
before you register widgets.
"""
class WidgetRegistry:
    _widget_registry: Dict[str, WidgetReference] = {}
    _widget_registration_events: Dict[str, asyncio.Event] = {} # for waiting until a widget got registered
    _enabled = False
    _polling_task: Optional[asyncio.Task] = None

    @staticmethod
    def register_widget(widget: tk.Widget, widget_name: str, parent_widget_name: Optional[str] = None):
        if WidgetRegistry._enabled:
            key = (parent_widget_name + "." + widget_name) if parent_widget_name else widget_name
            WidgetRegistry._widget_registry[key] = WidgetReference(widget)

            if key not in WidgetRegistry._widget_registration_events:
                WidgetRegistry._widget_registration_events[key] = asyncio.Event()
            WidgetRegistry._widget_registration_events[key].set()

    @staticmethod
    def unregister_widget(widget_name: str, parent_widget_name: Optional[str] = None):
        if WidgetRegistry._enabled:
            key = (parent_widget_name + "." + widget_name) if parent_widget_name else widget_name
            if key in WidgetRegistry._widget_registry:
                del WidgetRegistry._widget_registry[key]
            if key in WidgetRegistry._widget_registration_events:
                WidgetRegistry._widget_registration_events[key].clear()

    @staticmethod
    def is_widget_registered(full_widget_name: str) -> bool:
        return full_widget_name in WidgetRegistry._widget_registry

    @staticmethod
    def get_widget(full_widget_name: str) -> tk.Widget:
        return WidgetRegistry._widget_registry[full_widget_name].widget

    @staticmethod
    async def wait_for_widget_to_be_registered(full_widget_name: str):
        if full_widget_name not in WidgetRegistry._widget_registration_events:
            WidgetRegistry._widget_registration_events[full_widget_name] = asyncio.Event()

        try:
            await WidgetRegistry._widget_registration_events[full_widget_name].wait()
        except asyncio.CancelledError:
            return

    @staticmethod
    async def wait_for_widget_to_change_text(full_widget_name: str) -> str:
        start_time = datetime.datetime.now()
        ref = WidgetRegistry._widget_registry[full_widget_name]

        if ref.last_time_text_has_changed < start_time and ref.text_has_changed.is_set():
            ref.text_has_changed.clear()

        await ref.text_has_changed.wait()
        ref.text_has_changed.clear()
        return ref.old_text_value

    @staticmethod
    def set_up():
        WidgetRegistry._enabled = True
        loop = asyncio.get_event_loop()
        WidgetRegistry._polling_task = loop.create_task(WidgetRegistry._polling_worker())

    @staticmethod
    async def clean_up():
        if WidgetRegistry._polling_task and WidgetRegistry._polling_task.cancel():
            await WidgetRegistry._polling_task
            WidgetRegistry._widget_registry.clear()
            WidgetRegistry._widget_registration_events.clear()

    @staticmethod
    def _poll_updates():
        for ref in WidgetRegistry._widget_registry.values():
            current_text = get_text_of_widget(ref.widget)
            if current_text != ref.old_text_value:
                ref.last_time_text_has_changed = datetime.datetime.now()
                ref.old_text_value = current_text
                ref.text_has_changed.set()

    @staticmethod
    async def _polling_worker():
        try:
            while True:
                await asyncio.sleep(0.1)
                WidgetRegistry._poll_updates()
        except asyncio.CancelledError:
            pass
