import pytest
import pytest_asyncio
from sonic_protocol.schema import DeviceType

from soniccontrol_gui.constants import ui_labels
from sonic_pytest.gui import widget_names
from sonic_pytest.gui.gui_controller import GuiController
from sonic_pytest.gui.workflows import (
    get_ramp_test_frequency_observation_settings,
    start_ramp_procedure,
)

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


@pytest.mark.allowed_devices(DeviceType.MVP_WORKER)
@pytest.mark.asyncio(loop_scope="package")
async def test_run_ramp_procedure():
    controller = GuiController()

    await start_ramp_procedure()

    expected_freq_changes, freq_change_timeout_s = get_ramp_test_frequency_observation_settings()
    observed_freq_labels: list[str] = []
    for _ in range(expected_freq_changes):
        observed_freq_labels.append(
            await controller.wait_for_widget_to_change_text(
                widget_names.STATUS_BAR_FREQ_LABEL,
                freq_change_timeout_s,
            )
        )

    assert len(set(observed_freq_labels)) == expected_freq_changes, (
        f"Expected {expected_freq_changes} distinct ramp frequency updates, got {observed_freq_labels}"
    )

    proc_running_label = await controller.wait_for_widget_text_to_equal(
        widget_names.PROC_CONTROLLING_RUNNING_PROC_LABEL,
        ui_labels.PROC_NOT_RUNNING,
        8.0,
    )
    assert proc_running_label == ui_labels.PROC_NOT_RUNNING, f"procedure still running: '{proc_running_label}'"

    status_proc_label = await controller.wait_for_widget_text_to_contain(
        widget_names.STATUS_BAR_PROCEDURE_LABEL,
        "none",
        3.0,
    )
    assert "none" in status_proc_label.lower()

    signal_label = await controller.wait_for_widget_text_to_contain(
        widget_names.STATUS_BAR_SIGNAL_LABEL,
        "off",
        3.0,
    )
    assert "off" in signal_label.lower()


@pytest.mark.allowed_devices(DeviceType.MVP_WORKER)
@pytest.mark.asyncio(loop_scope="package")
async def test_stop_ramp_procedure():
    controller = GuiController()

    await start_ramp_procedure()

    controller.press_button(widget_names.PROC_CONTROLLING_STOP_BUTTON)

    proc_running_label = await controller.wait_for_widget_text_to_equal(
        widget_names.PROC_CONTROLLING_RUNNING_PROC_LABEL,
        ui_labels.PROC_NOT_RUNNING,
        2.0,
    )
    assert proc_running_label == ui_labels.PROC_NOT_RUNNING, f"procedure still running: '{proc_running_label}'"

