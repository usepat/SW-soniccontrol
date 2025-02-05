import asyncio
from pathlib import Path
from typing import Any, Coroutine, Dict, List, Optional
import tkinter as tk
from async_tkinter_loop.async_tkinter_loop import main_loop
import ttkbootstrap as ttk
from robot.api.deco import keyword, library
import robot.api.logger as logger
from ttkbootstrap.utility import enable_high_dpi_awareness
from soniccontrol_gui.view import TabView
from soniccontrol_gui.views.core.connection_window import ConnectionWindow
from soniccontrol.system import PLATFORM, System
from soniccontrol_gui.utils.widget_registry import WidgetRegistry, get_text_of_widget, set_text_of_widget
from soniccontrol_gui.widgets.notebook import Notebook


# We want Suite as scope, so that the gui can be used across tests
# Because opening the app is time consuming
@library(auto_keywords=False, scope="SUITE")
class RobotSonicControlGui:
    def __init__(self):
        self._root: Optional[tk.Tk | tk.Toplevel] = None
        # Because robot is sync and the gui async, 
        # we have to embed the gui calls in the asyncio event loop
        self._loop = asyncio.get_event_loop()

    @keyword('Open app')
    def open_app(self, simulation_exe_path: str):
        WidgetRegistry.set_up()
        main_window = ConnectionWindow(Path(simulation_exe_path))
        if PLATFORM != System.WINDOWS:
            enable_high_dpi_awareness(main_window.view)
        self._root = main_window.view.winfo_toplevel()
        self._loop.create_task(main_loop(main_window.view))  # type: ignore

    @keyword('Close app')
    def close_app(self):
        if self._root is None:
            raise RuntimeError("Root was None")

        self._loop.run_until_complete(WidgetRegistry.clean_up()) # Maybe we can do this better. But Idk
        self._root.destroy()

    @keyword('Let the app update for "${time_ms}" ms')
    def sleep_update(self, time_ms: int):
        """
        This shit is needed, because the sleep function of the robot framework pauses the whole application,
        also the execution of the asyncio event loop
        """
        self._loop.run_until_complete(asyncio.sleep(time_ms / 1000))

    @keyword('Does the widget "${name_widget}" exist')
    def does_widget_exist(self, name_widget: str) -> bool:
        return WidgetRegistry.is_widget_registered(name_widget)

    @keyword('Wait up to "${timeout_ms}" ms for the widget "${name_widget}" to be registered')
    def wait_for_widget_to_be_registered(self, timeout_ms: int, name_widget: str) -> None:
        task = asyncio.wait_for(WidgetRegistry.wait_for_widget_to_be_registered(name_widget), timeout_ms / 1000.)
        self._loop.run_until_complete(task)
        
    @keyword('Wait up to "${timeout_ms}" ms for the widget "${name_widget}" to change text')
    def wait_for_widget_to_change(self, timeout_ms: int, name_widget: str) -> str:  
        task = asyncio.wait_for(WidgetRegistry.wait_for_widget_to_change_text(name_widget), timeout_ms / 1000.)
        changed_text = self._loop.run_until_complete(task)
        return changed_text

    @keyword('Wait up to "${timeout_ms}" ms for multiple widgets "${widget_names}" to change text')
    def wait_for_multiple_widgets_to_change_and_get_text(self, timeout_ms: int, widget_names: List[str]) -> Dict[str, str]:  
        tasks: List[Coroutine[Any, Any, str]] = []
        for widget_name in widget_names:
            task = WidgetRegistry.wait_for_widget_to_change_text(widget_name)
            tasks.append(task)
        
        async def collect_tasks(tasks):
            results = await asyncio.gather(*tasks)
            return {widget_name: result for widget_name, result in zip(widget_names, results)}

        coroutine = asyncio.wait_for(collect_tasks(tasks), timeout=timeout_ms / 1000.)
        changed_texts = self._loop.run_until_complete(coroutine)
        return changed_texts

    @keyword('Get text of widget "${name_widget}"')
    def get_widget_text(self, name_widget: str) -> str:         
        widget = WidgetRegistry.get_widget(name_widget)
        return get_text_of_widget(widget)

    @keyword('Set text of widget "${name_widget}" to "${text}"')
    def set_widget_text(self, name_widget: str, text: str) -> None:
        widget = WidgetRegistry.get_widget(name_widget)
        set_text_of_widget(widget, text)

    @keyword('Press button "${name_widget}"')
    def press_button(self, name_widget: str) -> None:
        widget = WidgetRegistry.get_widget(name_widget)
        if isinstance(widget, (tk.Button, ttk.Button, ttk.Checkbutton)):
            widget.invoke()
        else:
            raise TypeError(f"The registered object '{name_widget}' is not a button")
        
    @keyword('Switch to tab "${tab_widget}"')
    def switch_to_tab(self, tab_widget: str) -> None:
        tab_view = WidgetRegistry.get_widget(tab_widget)
        if not isinstance(tab_view, TabView):
            raise TypeError(f"The registered object '{tab_widget}' is not a tab view")

        parent_name = tab_widget.split(".")[0]
        notebook = WidgetRegistry.get_widget(parent_name)
        if not isinstance(notebook, (Notebook, ttk.Notebook)):
            raise TypeError(f"The registered object '{parent_name}' is not a notebook")
        notebook.select(tab_view)

    @keyword('Get text of "${index_child}"th child of widget "${name_widget}"')
    def get_text_of_widget_child(self, index_child: int, name_widget: str) -> str:   
        """
            @brief gets the text of the ith child of the widget.
            @usage Useful for inspecting the monitor tab.
        """      
        widget = WidgetRegistry.get_widget(name_widget)
        child = widget.winfo_children()[index_child]
        return get_text_of_widget(child)             


