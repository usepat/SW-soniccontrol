import asyncio
import tkinter as tk
from typing import List
import ttkbootstrap as ttk

from soniccontrol_gui.utils.widget_registry import WidgetRegistry, get_text_of_widget, set_text_of_widget
from soniccontrol_gui.view import TabView
from soniccontrol_gui.widgets.notebook import Notebook


class GuiController:
    def is_widget_registered(self, widget_name: str) -> bool:
        return WidgetRegistry.is_widget_registered(widget_name)
    
    async def wait_for_widget_to_be_registered(self, widget_name: str, timeout_s: float | None = None):
        await asyncio.wait_for(WidgetRegistry.wait_for_widget_to_be_registered(widget_name), timeout_s)

    async def wait_for_widget_to_change_text(self, widget_name: str, timeout_s: float | None = None):
        return await asyncio.wait_for(WidgetRegistry.wait_for_widget_to_change_text(widget_name), timeout_s)
    
    async def wait_for_multiple_widgets_to_change_text(self, *widget_names: str, timeout_s: float | None = None) -> List[str]:
        coroutines = [ 
            asyncio.wait_for(WidgetRegistry.wait_for_widget_to_change_text(widget_name), timeout_s) 
            for widget_name in widget_names
        ]
        return await asyncio.gather(*coroutines)

    def get_widget_text(self, widget_name: str) -> str:
        widget = WidgetRegistry.get_widget(widget_name)
        return get_text_of_widget(widget)
    
    def set_widget_text(self, widget_name: str, text: str) -> None:
        widget = WidgetRegistry.get_widget(widget_name)
        set_text_of_widget(widget, text)

    def press_button(self, widget_name: str):
        widget = WidgetRegistry.get_widget(widget_name)
        if isinstance(widget, (tk.Button, ttk.Button, ttk.Checkbutton)):
            widget.invoke()
        else:
            raise TypeError(f"The registered object '{widget_name}' is not a button")

    def switch_to_tab(self, widget_name: str) -> None:
        tab_view = WidgetRegistry.get_widget(widget_name)
        if not isinstance(tab_view, TabView):
            raise TypeError(f"The registered object '{widget_name}' is not a tab view")

        parent_name = widget_name.split(".")[0]
        notebook = WidgetRegistry.get_widget(parent_name)
        if not isinstance(notebook, (Notebook, ttk.Notebook)):
            raise TypeError(f"The registered object '{parent_name}' is not a notebook")
        notebook.select(tab_view)

    def get_text_of_widget_child(self, widget_name: str, index_child: int) -> str:   
        """
            @brief gets the text of the ith child of the widget.
            @usage Useful for inspecting the monitor tab.
        """      
        widget = WidgetRegistry.get_widget(widget_name)
        assert isinstance(widget, tk.Widget), "widget has to be an instance or subclass of tk.Widget"
        child = widget.winfo_children()[index_child]
        return get_text_of_widget(child) 

    async def execute_events_until_idle(self, max_iter=10):
        root = WidgetRegistry.root
        assert root is not None, "root was not set on WidgetRegistry"
        for _ in range(max_iter):
            root.update_idletasks()
            root.update()
            await asyncio.sleep(0) # basically yields, and lets the event loop run. Cooperative scheduling  

    def clear_text_changed_flags(self):
        WidgetRegistry.clear_text_changed_flags()

    def clear_text_changed_flag_of_widget(self, widget_name: str):
        WidgetRegistry.clear_widget_text_changed_flag(widget_name)