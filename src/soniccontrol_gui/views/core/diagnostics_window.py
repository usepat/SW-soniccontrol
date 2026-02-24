import logging
from pathlib import Path
from typing import Callable, List
import asyncio
from async_tkinter_loop import async_handler
from ttkbootstrap.scrolled import ScrolledFrame
from soniccontrol.hw_tests.test_base import TestInteraction, TestResult
from soniccontrol.events import Event, PropertyChangeEvent
from soniccontrol.hw_tests.test_base import SemiAutomatedStep, TestInfo
from soniccontrol.hw_tests.test_executor import TestExecutor
from soniccontrol.hw_tests.test_report_writer import TestReportWriter
from soniccontrol.sonic_device import SonicDevice
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.view import TabView, View
from soniccontrol_gui.views.control.logging import Logging
from soniccontrol_gui.views.control.serialmonitor import SerialMonitor
from soniccontrol_gui.views.core.app_state import AppState, ExecutionState
from soniccontrol_gui.views.core.device_window import DeviceWindow, DeviceWindowView
import ttkbootstrap as ttk
from soniccontrol_gui.constants import ui_labels, sizes
from soniccontrol_gui.resources import images
from soniccontrol_gui.widgets.file_browse_button import FileBrowseButtonView
from soniccontrol_gui.widgets.message_box import DialogOptions, MessageBox
from soniccontrol_gui.widgets.test_widget import TestWidget



class HwTestingTab(UIComponent):
    def __init__(self, parent: UIComponent, test_executor: TestExecutor):
        self._logger = logging.getLogger(parent.logger.name + "." + HwTestingTab.__name__)

        self._test_executor = test_executor

        self._view = HwTestingTabView(parent.view)
        self._test_discovery_task = asyncio.create_task(self._discover_tests())
        self._test_widgets: List[TestWidget] = []
        self._tests: List[TestInfo] = []
        self._run_all_tests_task: asyncio.Task | None = None
        super().__init__(parent, self._view, self._logger)

        self._test_executor.subscribe(TestExecutor.NEEDS_USER_INTERACTION_EVENT, self._on_user_interaction_needed)
        self._test_executor.subscribe_property_listener(TestExecutor.RUNNING_TEST_INDEX_PROPERTY, self._on_running_test_index_changed)
        self._view.set_run_all_tests_callback(self._on_run_all_tests)
        self._view.set_stop_callback(self._on_stop_all_tests)
        self._view.set_create_test_report_callback(self._on_create_test_report)

    def _is_running_all_tests(self) -> bool:
        return not (self._run_all_tests_task is None or self._run_all_tests_task.done())

    def _on_running_test_index_changed(self, e: PropertyChangeEvent):
        running_test_index = e.new_value
        is_a_test_running = running_test_index is not None
        is_running_tests = self._is_running_all_tests()
        self._view.enable_stop_button(is_running_tests)
        self._view.enable_run_all_tests_button(not is_a_test_running and not is_running_tests)
            
    async def _discover_tests(self):
        self._tests = await self._test_executor.load_tests()
        for test_info in self._tests:
            test_widget = TestWidget(self, self._view.tests_frame, test_info)

            test_widget.subscribe(TestWidget.RUN_TEST_EVENT, self._on_run_test_with_index)
            test_widget.subscribe(TestWidget.STOP_TEST_EVENT, self._stop_test)
            self._test_executor.subscribe_property_listener(TestExecutor.RUNNING_TEST_INDEX_PROPERTY, test_widget.on_running_test_index_changed)

            self._test_widgets.append(test_widget)
        self._view.update_idletasks() # is needed to update the scroll view, so that it shows the widgets inside

    def _on_run_test_with_index(self, e: Event):
        test = e.data["test"]
        self._test_executor.run_test(test)

    def _on_run_all_tests(self):
        assert not self._is_running_all_tests(), "there is already this task running"

        self._run_all_tests_task = asyncio.create_task(self._run_all_tests())

    async def _run_all_tests(self):
        try:
            for test_widget in self._test_widgets:
                test_widget.enable(False)

            for test in self._tests:
                await self._test_executor.await_run_test(test)

        finally:
            for test_widget in self._test_widgets:
                test_widget.enable(True) # FIXME: if it is actually enabled depends on the app state

            self._view.enable_run_all_tests_button(True)
            self._view.enable_stop_button(False)

    @async_handler
    async def _on_stop_all_tests(self):
        if self._is_running_all_tests():
            assert self._run_all_tests_task is not None
            self._run_all_tests_task.cancel()
            await self._run_all_tests_task


    @async_handler
    async def _stop_test(self, _):
        await self._test_executor.stop_test()

    @async_handler
    async def _on_user_interaction_needed(self, event: Event):
        semi_automated_step: SemiAutomatedStep = event.data["semi_automated_step"]
        test: TestInfo = event.data["test"]

        if semi_automated_step.interaction == TestInteraction.PHYSICAL_INTERACTION:
            msg_box = MessageBox(self._view.root, semi_automated_step.message, ui_labels.USER_INTERACTION_NEEDED, [DialogOptions.PROCEED])
            answer = await msg_box.wait_for_answer()
            if answer is None or answer != DialogOptions.PROCEED:
                return # in case the window was closed, do not proceed the test. Do nothing
        elif semi_automated_step.interaction == TestInteraction.VALIDATION:
            msg_box = MessageBox(self._view.root, semi_automated_step.message, ui_labels.USER_INTERACTION_NEEDED, [DialogOptions.YES, DialogOptions.NO])
            answer = await msg_box.wait_for_answer()
            did_test_pass =  answer == DialogOptions.YES
            test.test_result = TestResult(did_test_pass, "Success" if did_test_pass else "Failure")
        else:
            raise NotImplementedError("This user interaction type was not implemented")

        self._test_executor.proceed_semi_automated_test()

    def on_execution_state_changed(self, e: PropertyChangeEvent) -> None:
        execution_state: ExecutionState = e.new_value.execution_state
        enabled = execution_state != ExecutionState.NOT_RESPONSIVE
        for test_widget in self._test_widgets:
            test_widget.enable(enabled)
            self._view.enable_run_all_tests_button(enabled)
            self._view.enable_stop_button(enabled)
        # TODO: stop tests

    def _on_create_test_report(self):
        file_path = self._view.file_path_test_report
        if file_path is None:
            MessageBox.show_error(self._view.root, "You have to specify a path first for the test report")
            return 
        
        TestReportWriter.write_test_report(self._tests, file_path)
        MessageBox.show_ok(self._view.root, f"Finished executing tests. Wrote report to '{str(file_path)}'")



class DiagnosticsWindow(DeviceWindow):
    def __init__(self, device: SonicDevice, root, connection_name: str):
        self._logger: logging.Logger = logging.getLogger(connection_name + ".ui")
        try:
            self._device = device
            self._view = DeviceWindowView(root=root, title=f"Device Window - Diagnostics Tool - {connection_name}")
            super().__init__(self._logger, self._view, self._device.communicator)

            self._serialmonitor = SerialMonitor(self, self._device.communicator)
            self._logging = Logging(self, connection_name)
            self._test_executor = TestExecutor(self._device)
            self._testing_tab = HwTestingTab(self, self._test_executor)

            self._view.add_tab_views([
                self._testing_tab.view,
                self._serialmonitor.view,
            ], right_one=False)
            self._view.add_tab_views([
                self._logging.view
            ], right_one=True)

            self.app_state.subscribe_property_listener(AppState.APP_EXECUTION_CONTEXT_PROP_NAME, self._serialmonitor.on_execution_state_changed)
            self.app_state.subscribe_property_listener(AppState.APP_EXECUTION_CONTEXT_PROP_NAME, self._testing_tab.on_execution_state_changed)

        except Exception as e:
            self._logger.error(e)
            MessageBox.show_error(root, str(e))
            raise



class HwTestingTabView(TabView):
    def __init__(self, master: ttk.Frame, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    @property
    def image(self) -> ttk.ImageTk.PhotoImage:
        return ImageLoader.load_image_resource(images.HOME_ICON_BLACK, sizes.TAB_ICON_SIZE)

    @property
    def tab_title(self) -> str:
        return ui_labels.HOME_LABEL

    def _initialize_children(self) -> None:
        self._scroll_frame = ScrolledFrame(self)
        self._test_frame = ttk.Frame(self._scroll_frame)
        self._control_frame = ttk.Frame(self)
        self._run_all_tests_button = ttk.Button(self, text=ui_labels.RUN_ALL_TESTS)
        self._stop_button = ttk.Button(self, text=ui_labels.STOP_LABEL)
        self._file_path_button = FileBrowseButtonView(self, "TestingTab", text=ui_labels.SPECIFY_PATH_LABEL)
        self._create_report_button = ttk.Button(self, text=ui_labels.CREATE_TEST_REPORT)

    def _initialize_publish(self) -> None:
        self._scroll_frame.pack(fill=ttk.BOTH, expand=True, padx=sizes.MEDIUM_PADDING, pady=sizes.MEDIUM_PADDING)
        self._test_frame.pack(fill=ttk.BOTH, expand=True, padx=sizes.LARGE_PADDING, pady=sizes.LARGE_PADDING)
        self._control_frame.pack(side=ttk.BOTTOM, fill=ttk.X, padx=sizes.LARGE_PADDING, pady=sizes.LARGE_PADDING)
        self._run_all_tests_button.pack(side=ttk.LEFT, padx=sizes.SMALL_PADDING)
        self._stop_button.pack(side=ttk.LEFT, padx=sizes.SMALL_PADDING)
        self._file_path_button.pack(side=ttk.LEFT, padx=sizes.SMALL_PADDING)
        self._create_report_button.pack(side=ttk.LEFT, padx=sizes.SMALL_PADDING)

    @property
    def tests_frame(self) -> View:
        return self._test_frame # type: ignore
    
    @property
    def file_path_test_report(self) -> Path | None:
        return self._file_path_button.path

    def set_run_all_tests_callback(self, callback: Callable[[], None]):
        self._run_all_tests_button.configure(command=callback)

    def set_stop_callback(self, callback: Callable[[], None]):
        self._stop_button.configure(command=callback)

    def set_create_test_report_callback(self, callback: Callable[[], None]):
        self._create_report_button.configure(command=callback)

    def enable_run_all_tests_button(self, enabled: bool):
        self._run_all_tests_button.configure(state=ttk.NORMAL if enabled else ttk.DISABLED)

    def enable_stop_button(self, enabled: bool):
        self._stop_button.configure(state=ttk.NORMAL if enabled else ttk.DISABLED)
