import asyncio
import tkinter as tk
from typing import Callable, ClassVar, List, cast
import ttkbootstrap as ttk

from soniccontrol_gui.utils.widget_registry import WidgetRegistry, get_text_of_widget, set_text_of_widget
from soniccontrol_gui.view import TabView
from soniccontrol_gui.widgets.notebook import Notebook


class GuiController:
    _pending_action_tasks: ClassVar[set[asyncio.Task[object]]] = set()

    def _refresh_ui_state(self) -> None:
        root = WidgetRegistry.root
        if root is not None:
            root.update_idletasks()
        WidgetRegistry.refresh_widget_texts()

    @classmethod
    def _track_new_tasks(cls, tasks: set[asyncio.Task[object]]) -> None:
        for task in tasks:
            cls._pending_action_tasks.add(task)
            task.add_done_callback(cls._pending_action_tasks.discard)

    @classmethod
    def _prune_pending_tasks(cls) -> None:
        cls._pending_action_tasks = {task for task in cls._pending_action_tasks if not task.done()}

    async def _wait_for_pending_action_progress(self, timeout_s: float | None) -> None:
        self._prune_pending_tasks()
        if not self._pending_action_tasks:
            await asyncio.sleep(WidgetRegistry._poll_interval_s)
            return

        if timeout_s is not None and timeout_s <= 0:
            raise asyncio.TimeoutError()

        wait_timeout = WidgetRegistry._poll_interval_s if timeout_s is None else min(timeout_s, WidgetRegistry._poll_interval_s)
        done, _ = await asyncio.wait(self._pending_action_tasks, timeout=wait_timeout, return_when=asyncio.FIRST_COMPLETED)
        self._prune_pending_tasks()

        for task in done:
            task.result()

    async def wait_for_pending_actions(self, timeout_s: float | None = None) -> None:
        deadline = None if timeout_s is None else asyncio.get_running_loop().time() + timeout_s

        while True:
            await self.execute_events_until_idle(1)
            self._prune_pending_tasks()
            if not self._pending_action_tasks:
                return

            remaining_timeout = None if deadline is None else max(0.0, deadline - asyncio.get_running_loop().time())
            await self._wait_for_pending_action_progress(remaining_timeout)

    def is_widget_registered(self, widget_name: str) -> bool:
        return WidgetRegistry.is_widget_registered(widget_name)
    
    async def wait_for_widget_to_be_registered(self, widget_name: str, timeout_s: float | None = None):
        await asyncio.wait_for(WidgetRegistry.wait_for_widget_to_be_registered(widget_name), timeout_s)

    async def wait_for_widget_to_change_text(self, widget_name: str, timeout_s: float | None = None):
        previous_text = self.get_widget_text(widget_name)
        deadline = None if timeout_s is None else asyncio.get_running_loop().time() + timeout_s

        while True:
            await self.execute_events_until_idle(1)
            current_text = self.get_widget_text(widget_name)
            if current_text != previous_text:
                return current_text

            remaining_timeout = None if deadline is None else max(0.0, deadline - asyncio.get_running_loop().time())
            wait_timeout = WidgetRegistry._poll_interval_s if remaining_timeout is None else min(remaining_timeout, WidgetRegistry._poll_interval_s)
            if wait_timeout <= 0:
                raise asyncio.TimeoutError()

            try:
                changed_text = await asyncio.wait_for(
                    WidgetRegistry.wait_for_widget_to_change_text(widget_name),
                    wait_timeout,
                )
            except asyncio.TimeoutError:
                continue

            if changed_text != previous_text:
                return changed_text
    
    async def wait_for_multiple_widgets_to_change_text(self, *widget_names: str, timeout_s: float | None = None) -> List[str]:
        coroutines = [ 
            asyncio.wait_for(self.wait_for_widget_to_change_text(widget_name, timeout_s), timeout_s)
            for widget_name in widget_names
        ]
        return await asyncio.gather(*coroutines)

    async def wait_for_widget_text(self, widget_name: str, predicate: Callable[[str], bool], timeout_s: float | None = None) -> str:
        deadline = None if timeout_s is None else asyncio.get_running_loop().time() + timeout_s

        while True:
            await self.execute_events_until_idle(1)
            text = self.get_widget_text(widget_name)
            if predicate(text):
                return text

            remaining_timeout = None if deadline is None else max(0.0, deadline - asyncio.get_running_loop().time())
            await self._wait_for_pending_action_progress(remaining_timeout)

    async def wait_for_widget_text_to_contain(self, widget_name: str, expected_text: str, timeout_s: float | None = None) -> str:
        return await self.wait_for_widget_text(widget_name, lambda current_text: expected_text in current_text, timeout_s)

    async def wait_for_widget_text_to_equal(self, widget_name: str, expected_text: str, timeout_s: float | None = None) -> str:
        return await self.wait_for_widget_text(widget_name, lambda current_text: current_text == expected_text, timeout_s)

    async def wait_for_widget_text_to_stay_equal(self, widget_name: str, duration_s: float) -> str:
        expected_text = self.get_widget_text(widget_name)
        deadline = asyncio.get_running_loop().time() + duration_s

        while True:
            await self.execute_events_until_idle(1)
            current_text = self.get_widget_text(widget_name)
            if current_text != expected_text:
                raise AssertionError(
                    f"Expected widget '{widget_name}' text to stay '{expected_text}', but got '{current_text}'"
                )

            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                return expected_text

            await self._wait_for_pending_action_progress(remaining)

    def get_widget_text(self, widget_name: str) -> str:
        widget = WidgetRegistry.get_widget(widget_name)
        return get_text_of_widget(widget)
    
    def set_widget_text(self, widget_name: str, text: str) -> None:
        widget = WidgetRegistry.get_widget(widget_name)
        set_text_of_widget(widget, text)
        self._refresh_ui_state()

    def press_button(self, widget_name: str):
        widget = WidgetRegistry.get_widget(widget_name)
        if isinstance(widget, (tk.Button, ttk.Button, ttk.Checkbutton, tk.Checkbutton)):
            current_task = asyncio.current_task()
            tasks_before = set(asyncio.all_tasks())
            widget.invoke()
            tasks_after = set(asyncio.all_tasks())
            new_tasks = {
                cast(asyncio.Task[object], task)
                for task in tasks_after - tasks_before
                if task is not current_task and not task.done()
            }
            self._track_new_tasks(new_tasks)
            self._refresh_ui_state()
        else:
            raise TypeError(f"The registered object '{widget_name}' is not a button")

    def set_check_button_state(self, widget_name: str, state: bool):
        widget = WidgetRegistry.get_widget(widget_name)
        if isinstance(widget, (ttk.Checkbutton, tk.Checkbutton)):
            var_name = widget.cget("variable")
            widget.setvar(var_name, "1" if state else "0")
            self._refresh_ui_state()
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
        self._refresh_ui_state()

    def get_text_of_widget_child(self, widget_name: str, index_child: int) -> str:   
        """
            @brief gets the text of the ith child of the widget.
            @usage Useful for inspecting the monitor tab.
        """      
        widget = WidgetRegistry.get_widget(widget_name)
        assert isinstance(widget, tk.Widget), "widget has to be an instance or subclass of tk.Widget"
        child = cast(tk.Widget | tk.Variable, widget.winfo_children()[index_child])
        return get_text_of_widget(child) 

    def get_texts_of_widget_children(self, widget_name: str) -> list[str]:
        widget = WidgetRegistry.get_widget(widget_name)
        assert isinstance(widget, tk.Widget), "widget has to be an instance or subclass of tk.Widget"
        children = cast(list[tk.Widget | tk.Variable], widget.winfo_children())
        return [get_text_of_widget(child) for child in children]

    async def execute_events_until_idle(self, max_iter=10):
        root = WidgetRegistry.root
        assert root is not None, "root was not set on WidgetRegistry"
        for _ in range(max_iter):
            root.update_idletasks()
            root.update()
            WidgetRegistry.refresh_widget_texts()
            await asyncio.sleep(0) # basically yields, and lets the event loop run. Cooperative scheduling  

    def clear_text_changed_flags(self):
        WidgetRegistry.clear_text_changed_flags()

    def clear_text_changed_flag_of_widget(self, widget_name: str):
        WidgetRegistry.clear_widget_text_changed_flag(widget_name)