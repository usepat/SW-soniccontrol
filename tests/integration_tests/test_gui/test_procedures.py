import pytest
from soniccontrol_gui.utils.testing import widget_names
from soniccontrol_gui.utils.testing.gui_controller import GuiController
import asyncio
import pytest_asyncio
from soniccontrol_gui.constants import ui_labels
from soniccontrol_gui.utils.testing.workflows import proceed_without_experiment, start_ramp_procedure

@pytest_asyncio.fixture(scope="function", loop_scope="package", autouse=True)
async def procedure_tab_fixture():
    controller = GuiController()
    controller.switch_to_tab(widget_names.PROCEDURES_TAB)

    controller.clear_text_changed_flags()

    yield

    running_proc_label = controller.get_widget_text(widget_names.PROC_CONTROLLING_RUNNING_PROC_LABEL)
    if running_proc_label != ui_labels.PROC_NOT_RUNNING:
        controller.press_button(widget_names.PROC_CONTROLLING_STOP_BUTTON)

    controller.set_widget_text(widget_names.PROC_CONTROLLING_PROCEDURE_COMBOBOX, "Ramp")
    await controller.execute_events_until_idle()
    controller.clear_text_changed_flags()



@pytest.mark.asyncio(loop_scope="package")
async def test_run_ramp_procedure():
    controller = GuiController()

    controller.clear_text_changed_flag_of_widget(widget_names.STATUS_BAR_SIGNAL_LABEL)
    await start_ramp_procedure()

    timeout = 1.5
    for _ in range(11):
        # wait_for_widget_to_change_text automatically clears the text changed flag
        signal_label = await controller.wait_for_widget_to_change_text(widget_names.STATUS_BAR_SIGNAL_LABEL, timeout)
        assert "on" in signal_label

        signal_label = await controller.wait_for_widget_to_change_text(widget_names.STATUS_BAR_SIGNAL_LABEL, timeout)
        assert "off" in signal_label

    proc_running_label = await controller.wait_for_widget_to_change_text(widget_names.PROC_CONTROLLING_RUNNING_PROC_LABEL, 2.5)
    assert proc_running_label == ui_labels.PROC_NOT_RUNNING, f"procedure still running: '{proc_running_label}'"


@pytest.mark.asyncio(loop_scope="package")
async def test_stop_ramp_procedure():
    controller = GuiController()

    await start_ramp_procedure()

    controller.press_button(widget_names.PROC_CONTROLLING_STOP_BUTTON)

    proc_running_label = await controller.wait_for_widget_to_change_text(widget_names.PROC_CONTROLLING_RUNNING_PROC_LABEL, 2.0)
    assert proc_running_label == ui_labels.PROC_NOT_RUNNING, f"procedure still running: '{proc_running_label}'"

