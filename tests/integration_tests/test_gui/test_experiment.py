import pytest
import asyncio
from soniccontrol_gui.utils.testing import widget_names
from soniccontrol_gui.utils.testing.gui_controller import GuiController
from soniccontrol_gui.constants import ui_labels
import pytest_asyncio
from soniccontrol_gui.utils.testing.workflows import fill_out_experiment_data, send_over_serial_monitor, start_ramp_capture, start_spectrum_measure_capture


@pytest_asyncio.fixture(scope="function", loop_scope="package", autouse=True)
async def experiment_tab_fixture():
    controller = GuiController()
    controller.switch_to_tab(widget_names.MEASURING_TAB)
    controller.clear_text_changed_flags()

    yield

    controller.clear_text_changed_flags()


@pytest.mark.asyncio(loop_scope="package")
async def test_experiment_control_button():
    controller = GuiController()

    label_control_button = controller.get_widget_text(widget_names.MEASURING_CONTROL_BUTTON)
    assert label_control_button == ui_labels.NEW_EXPERIMENT
    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)
    await controller.execute_events_until_idle()

    fill_out_experiment_data()
    label_control_button = controller.get_widget_text(widget_names.MEASURING_CONTROL_BUTTON)
    assert label_control_button == ui_labels.FINISH_LABEL
    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)
    await controller.execute_events_until_idle()

    label_control_button = controller.get_widget_text(widget_names.MEASURING_CONTROL_BUTTON)
    assert label_control_button == ui_labels.SELECTED
    controller.set_widget_text(widget_names.MEASURING_TARGET_COMBOBOX, "Free")
    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)
    await controller.execute_events_until_idle()

    label_control_button = controller.get_widget_text(widget_names.MEASURING_CONTROL_BUTTON)
    assert label_control_button == ui_labels.START_CAPTURE
    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)
    await controller.execute_events_until_idle()

    label_control_button = controller.get_widget_text(widget_names.MEASURING_CONTROL_BUTTON)
    assert label_control_button == ui_labels.END_CAPTURE
    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)
    await controller.execute_events_until_idle()

    label_control_button = controller.get_widget_text(widget_names.MEASURING_CONTROL_BUTTON)
    assert label_control_button == ui_labels.NEW_EXPERIMENT


@pytest.mark.asyncio(loop_scope="package")
async def test_experiment_capture_ends_if_procedure_finishes():
    await start_ramp_capture()
    await asyncio.sleep(2)

    await send_over_serial_monitor("!stop")

    controller = GuiController()
    label_control_button = await controller.wait_for_widget_to_change_text(widget_names.MEASURING_CONTROL_BUTTON, 2.0)
    assert label_control_button == ui_labels.NEW_EXPERIMENT

@pytest.mark.asyncio(loop_scope="package")
async def test_procedure_stops_if_capture_ends():
    await start_ramp_capture()
    await asyncio.sleep(2)

    controller = GuiController()
    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)
    
    proc_label, label_control_button = await controller.wait_for_multiple_widgets_to_change_text(
        widget_names.STATUS_BAR_PROCEDURE_LABEL, widget_names.MEASURING_CONTROL_BUTTON, 
        timeout_s=2.0
    )

    assert label_control_button == ui_labels.NEW_EXPERIMENT
    assert "none" in proc_label

@pytest.mark.asyncio(loop_scope="package")
async def test_experiment_capture_ends_if_spectrum_measure_finishes():
    await start_spectrum_measure_capture()

    controller = GuiController()
    label_control_button = await controller.wait_for_widget_to_change_text(widget_names.MEASURING_CONTROL_BUTTON, 15.0)
    assert label_control_button == ui_labels.NEW_EXPERIMENT

@pytest.mark.asyncio(loop_scope="package")
async def test_spectrum_measure_stops_if_capture_ends():
    await start_spectrum_measure_capture()
    await asyncio.sleep(2)

    controller = GuiController()
    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)
    label_control_button = await controller.wait_for_widget_to_change_text(widget_names.MEASURING_CONTROL_BUTTON, 2.0)
    assert label_control_button == ui_labels.NEW_EXPERIMENT

    # This check ensures that spectrum measure is really turned off
    # and is not still running in the background
    await asyncio.sleep(2)
    label_freq1 = controller.get_widget_text(widget_names.STATUS_BAR_FREQ_LABEL)
    await asyncio.sleep(5)
    label_freq2 = controller.get_widget_text(widget_names.STATUS_BAR_FREQ_LABEL)
    assert label_freq1 == label_freq2


