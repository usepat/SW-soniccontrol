import pytest
import asyncio
from sonic_protocol.schema import DeviceType
from sonic_pytest.gui import widget_names
from sonic_pytest.gui.gui_controller import GuiController
from soniccontrol_gui.constants import ui_labels
import pytest_asyncio
from sonic_pytest.gui.workflows import fill_out_experiment_data, send_over_serial_monitor, start_ramp_capture, start_spectrum_measure_capture


async def reset_experiment_state(device_window=None) -> None:
    controller = GuiController()
    controller.switch_to_tab(widget_names.MEASURING_TAB)

    await send_over_serial_monitor("!stop")
    await send_over_serial_monitor("!OFF")
    await controller.execute_events_until_idle()

    for _ in range(4):
        label_control_button = controller.get_widget_text(widget_names.MEASURING_CONTROL_BUTTON)
        if label_control_button == ui_labels.NEW_EXPERIMENT:
            return
        if label_control_button == ui_labels.END_CAPTURE:
            capture = None if device_window is None else getattr(device_window, "_capture", None)
            if capture is not None:
                await capture.end_capture()
            else:
                controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)
            await controller.wait_for_widget_text(
                widget_names.MEASURING_CONTROL_BUTTON,
                lambda current_text: current_text != ui_labels.END_CAPTURE,
                5.0,
            )
            await controller.execute_events_until_idle()
            continue
        if label_control_button == ui_labels.START_CAPTURE:
            controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)
            await controller.wait_for_widget_text(
                widget_names.MEASURING_CONTROL_BUTTON,
                lambda current_text: current_text != ui_labels.START_CAPTURE,
                5.0,
            )
            await controller.execute_events_until_idle()
            continue

        controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)
        await controller.execute_events_until_idle()

        if label_control_button == ui_labels.FINISH_LABEL:
            fill_out_experiment_data()
            await controller.execute_events_until_idle()
        elif label_control_button == ui_labels.SELECTED:
            controller.set_widget_text(widget_names.MEASURING_TARGET_COMBOBOX, "Free")
            await controller.execute_events_until_idle()

    raise AssertionError("Could not reset experiment state to 'New Experiment'")


@pytest_asyncio.fixture(scope="function", loop_scope="package", autouse=True)
async def experiment_tab_fixture(device_window):
    controller = GuiController()
    controller.switch_to_tab(widget_names.MEASURING_TAB)
    await reset_experiment_state(device_window)
    controller.clear_text_changed_flags()

    yield

    await reset_experiment_state(device_window)
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


@pytest.mark.allowed_devices(DeviceType.MVP_WORKER)
@pytest.mark.asyncio(loop_scope="package")
async def test_experiment_capture_ends_if_procedure_finishes():
    await start_ramp_capture()

    controller = GuiController()
    controller.clear_text_changed_flags()

    await send_over_serial_monitor("!stop")

    label_control_button = await controller.wait_for_widget_text_to_equal(
        widget_names.MEASURING_CONTROL_BUTTON,
        ui_labels.NEW_EXPERIMENT,
        2.0,
    )
    assert label_control_button == ui_labels.NEW_EXPERIMENT


@pytest.mark.allowed_devices(DeviceType.MVP_WORKER)
@pytest.mark.asyncio(loop_scope="package")
async def test_procedure_stops_if_capture_ends():
    await start_ramp_capture()

    controller = GuiController()
    controller.clear_text_changed_flags()
    
    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)
    
    proc_label, label_control_button = await asyncio.gather(
        controller.wait_for_widget_text_to_contain(widget_names.STATUS_BAR_PROCEDURE_LABEL, "none", 2.0),
        controller.wait_for_widget_text_to_equal(widget_names.MEASURING_CONTROL_BUTTON, ui_labels.NEW_EXPERIMENT, 2.0),
    )

    assert label_control_button == ui_labels.NEW_EXPERIMENT
    assert "none" in proc_label


@pytest.mark.allowed_devices(DeviceType.MVP_WORKER)
@pytest.mark.asyncio(loop_scope="package")
async def test_experiment_capture_ends_if_spectrum_measure_finishes():
    await start_spectrum_measure_capture()

    controller = GuiController()
    label_control_button = await controller.wait_for_widget_text_to_equal(
        widget_names.MEASURING_CONTROL_BUTTON,
        ui_labels.NEW_EXPERIMENT,
        15.0,
    )
    assert label_control_button == ui_labels.NEW_EXPERIMENT


@pytest.mark.allowed_devices(DeviceType.MVP_WORKER)
@pytest.mark.skip_performance_monitor_check
@pytest.mark.asyncio(loop_scope="package")
async def test_spectrum_measure_stops_if_capture_ends(device_window):
    await start_spectrum_measure_capture()

    controller = GuiController()
    capture = getattr(device_window, "_capture", None)
    assert capture is not None
    await capture.end_capture()
    label_control_button = await controller.wait_for_widget_text_to_equal(
        widget_names.MEASURING_CONTROL_BUTTON,
        ui_labels.NEW_EXPERIMENT,
        2.0,
    )
    assert label_control_button == ui_labels.NEW_EXPERIMENT

    # This check ensures that spectrum measure is really turned off
    # and is not still running in the background.
    await controller.wait_for_widget_text_to_stay_equal(widget_names.STATUS_BAR_FREQ_LABEL, 5.0)

