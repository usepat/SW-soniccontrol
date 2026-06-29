import logging
from typing import Callable
from soniccontrol.events import Event, PropertyChangeEvent
from soniccontrol.hw_tests.test_base import TestInfo
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.view import View
import ttkbootstrap as ttk
from soniccontrol_gui.constants import ui_labels, sizes


class TestWidget(UIComponent):
    RUN_TEST_EVENT = "RUN_TEST"
    STOP_TEST_EVENT = "STOP_TEST"

    def __init__(self, parent: UIComponent, parent_slot: View, test_info: TestInfo):
        self._logger = logging.getLogger(parent.logger.name + "." + TestWidget.__name__)
        self._test_info = test_info
        self._run_button_enabled = False
        self._stop_button_enabled = False
        self._view = TestWidgetView(parent_slot, self._test_info.index, 
                                    self._test_info.suite_name, self._test_info.test_name)
        super().__init__(parent, self._view, self._logger)

        self._view.set_run_test_button_callback(self._on_run_test_clicked)
        self._view.set_stop_test_button_callback(self._on_stop_test_clicked)
        self._test_info.subscribe_property_listener("test_result", self._on_test_result_changed)

    def on_running_test_index_changed(self, e: PropertyChangeEvent):
        running_test_index = e.new_value
        is_a_test_running = running_test_index is not None
        is_this_test_running = is_a_test_running and running_test_index == self._test_info.index
        self._run_button_enabled = not is_a_test_running
        self._stop_button_enabled = is_this_test_running
        self._view.set_run_test_button_enabled(self._run_button_enabled)
        self._view.set_stop_test_button_enabled(self._stop_button_enabled)

    def _on_run_test_clicked(self):
        self.emit(Event(TestWidget.RUN_TEST_EVENT, test=self._test_info))

    def _on_stop_test_clicked(self):
        self.emit(Event(TestWidget.STOP_TEST_EVENT))

    def _on_test_result_changed(self, event: PropertyChangeEvent):
        test_result = event.new_value
        if test_result is None:
            self._view.test_result = ""
            self._view.set_color_test_result_label(ttk.PRIMARY)
        else:
            self._view.test_result = ui_labels.SUCCESS if test_result.success else (ui_labels.FAILURE + ": " + test_result.assertion_msg)
            self._view.set_color_test_result_label(ttk.SUCCESS if test_result.success else ttk.DANGER)

    def enable(self, enabled: bool):
        if enabled:
            self._view.set_run_test_button_enabled(self._run_button_enabled)
            self._view.set_stop_test_button_enabled(self._stop_button_enabled)
        else:
            self._view.set_run_test_button_enabled(False)
            self._view.set_stop_test_button_enabled(False)

class TestWidgetView(View):
    def __init__(self, master: ttk.Frame, index: int, suite_name: str, test_name: str, *args, **kwargs) -> None:
        self._suite_name = suite_name
        self._test_name = test_name
        self._index = index
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        self._suite_label = ttk.Label(self._master, text=self._suite_name)
        self._test_label = ttk.Label(self._master, text=self._test_name)
        
        self._test_result_text_var = ttk.StringVar(self._master, value="")
        self._test_result_label = ttk.Label(self._master, textvariable=self._test_result_text_var)

        self._run_test_button = ttk.Button(self._master, text=ui_labels.RUN_LABEL)
        self._stop_test_button = ttk.Button(self._master, text=ui_labels.STOP_LABEL)

    def _initialize_publish(self) -> None:
        self._master.columnconfigure(0, weight=sizes.DONT_EXPAND)
        self._master.columnconfigure(1, weight=sizes.DONT_EXPAND)
        self._master.columnconfigure(2, weight=sizes.EXPAND)
        self._master.columnconfigure(3, weight=sizes.DONT_EXPAND)
        self._master.columnconfigure(4, weight=sizes.DONT_EXPAND)
        self._master.rowconfigure(self._index, weight=sizes.EXPAND)

        self._suite_label.grid(row=self._index, column=0, sticky=ttk.NSEW, padx=sizes.SMALL_PADDING, pady=sizes.SMALL_PADDING)
        self._test_label.grid(row=self._index, column=1, sticky=ttk.NSEW, padx=sizes.SMALL_PADDING, pady=sizes.SMALL_PADDING)
        self._test_result_label.grid(row=self._index, column=2, sticky=ttk.NSEW, padx=sizes.SMALL_PADDING, pady=sizes.SMALL_PADDING)
        self._run_test_button.grid(row=self._index, column=3, sticky=ttk.NSEW, padx=sizes.SMALL_PADDING, pady=sizes.SMALL_PADDING)
        self._stop_test_button.grid(row=self._index, column=4, sticky=ttk.NSEW, padx=sizes.SMALL_PADDING, pady=sizes.SMALL_PADDING)
        
    @property
    def test_result(self) -> str:
        return self._test_result_text_var.get()
    
    @test_result.setter
    def test_result(self, value: str):
        self._test_result_text_var.set(value)

    def set_run_test_button_callback(self, callback: Callable[[], None]):
        self._run_test_button.configure(command=callback)

    def set_stop_test_button_callback(self, callback: Callable[[], None]):
        self._stop_test_button.configure(command=callback)

    def set_run_test_button_enabled(self, enabled: bool) -> None:
        self._run_test_button.configure(state=ttk.NORMAL if enabled else ttk.DISABLED)

    def set_stop_test_button_enabled(self, enabled: bool) -> None:
        self._stop_test_button.configure(state=ttk.NORMAL if enabled else ttk.DISABLED)

    def set_color_test_result_label(self, color: str) -> None:
        self._test_result_label.configure(bootstyle=color)
    