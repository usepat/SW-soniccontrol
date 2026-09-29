import asyncio

from soniccontrol.communication.postman_proxy_communicator import PostmanProxyCommunicator
from soniccontrol.sonic_device import SonicDevice
from soniccontrol_gui.constants import ui_labels
from soniccontrol_gui.views.control.serialmonitor import SerialMonitor
from sonic_pytest.gui import widget_names
from sonic_pytest.gui.gui_controller import GuiController


_active_gui_test_uses_postman_proxy = False


def configure_active_gui_test_device(device: SonicDevice | None) -> None:
    global _active_gui_test_uses_postman_proxy
    _active_gui_test_uses_postman_proxy = bool(
        device is not None and isinstance(device.communicator, PostmanProxyCommunicator)
    )


def _get_ramp_test_args() -> dict[str, str]:
    if _active_gui_test_uses_postman_proxy:
        return {
            "f_stop": "1.1",
            "t_on": "2500",
            "t_off": "2500",
        }

    return {
        "f_stop": "1.3",
        "t_on": "1000",
        "t_off": "1000",
    }


def get_ramp_test_frequency_observation_settings() -> tuple[int, float]:
    if _active_gui_test_uses_postman_proxy:
        return 2, 6.0

    return 3, 3.0


def get_serial_monitor_entries() -> list[str]:
    controller = GuiController()
    # the last entry is empty, because every line ends in \n. Therefore remove it
    return controller.get_widget_text(widget_names.SERIAL_MONITOR_TEXT).splitlines()[:-1]


def _extract_answer_after_command(entries: list[str], command_index: int, command: str, allow_fail: bool) -> str | None:
    for answer in entries[command_index + 1:]:
        if answer.startswith(">>>"):
            return None

        normalized_answer = answer.strip()
        if normalized_answer == "":
            continue

        assert not normalized_answer.startswith(SerialMonitor.COMMUNICATION_EXCEPTION_PREFIX), \
            f"Setup command '{command}' failed with communication error: {normalized_answer}"

        fields = normalized_answer.split("#")
        try:
            command_code = int(fields[0])
        except (IndexError, ValueError):
            continue

        assert allow_fail or command_code < 20000, f"Device returned error: {normalized_answer}"
        return normalized_answer

    return None

async def send_over_serial_monitor(command: str, allow_fail=False) -> str:
    controller = GuiController()
    controller.switch_to_tab(widget_names.SERIAL_MONITOR_TAB)
    existing_entries = get_serial_monitor_entries() 
    expected_command_entry = f">>> {command}"
    controller.set_widget_text(widget_names.SERIAL_MONITOR_COMMAND_LINE_INPUT_ENTRY, command)
    controller.press_button(widget_names.SERIAL_MONITOR_SEND_BUTTON)
    await controller.execute_events_until_idle()

    max_iter = 10
    for _ in range(max_iter):
        entries = get_serial_monitor_entries() 
        new_entries = entries[len(existing_entries):]
        if expected_command_entry not in new_entries:
            await controller.execute_events_until_idle()
            await asyncio.sleep(0.5)
            continue

        command_index = entries.index(expected_command_entry, len(existing_entries))
        answer = _extract_answer_after_command(entries, command_index, command, allow_fail)
        if answer is not None:
            return answer
        
        await controller.execute_events_until_idle()
        await asyncio.sleep(0.5)
    
    raise AssertionError("No answer could be received")


async def proceed_without_experiment():
    controller = GuiController()
    await controller.wait_for_widget_to_be_registered(widget_names.MESSAGE_BOX_OPTION_PROCEED, 2.0)
    controller.press_button(widget_names.MESSAGE_BOX_OPTION_PROCEED)


def set_ramp_args(
    *,
    f_start: str = "1",
    f_stop: str = "2",
    f_step: str = "100",
    t_on: str = "1000",
    t_off: str = "1000",
    gain: str = "100",
):
    controller = GuiController()
    # You have to set units before setting the values.
    # Some weird bug, probably units do not update the validity of the value, I guess
    # And with invalid args it will not start the procedure
    controller.set_widget_text(widget_names.RAMP_F_START_UNIT, "MHz")
    controller.set_widget_text(widget_names.RAMP_F_START, f_start)
    controller.set_widget_text(widget_names.RAMP_F_STOP_UNIT, "MHz")
    controller.set_widget_text(widget_names.RAMP_F_STOP, f_stop)
    controller.set_widget_text(widget_names.RAMP_F_STEP_UNIT, "kHz")
    controller.set_widget_text(widget_names.RAMP_F_STEP, f_step)
    controller.set_widget_text(widget_names.RAMP_T_ON_TIME, t_on)
    controller.set_widget_text(widget_names.RAMP_T_ON_UNIT, "ms")
    controller.set_widget_text(widget_names.RAMP_T_OFF_TIME, t_off)
    controller.set_widget_text(widget_names.RAMP_T_OFF_UNIT, "ms")
    controller.set_widget_text(widget_names.RAMP_GAIN, gain)


def set_spectrum_measure_args(
    *,
    gain: str = "50",
    f_start: str = "100000",
    f_stop: str = "110000",
    f_step: str = "1000",
    t_on: str = "1000",
    t_off: str = "0",
    t_offset: str = "0",
):
    controller = GuiController()
    controller.set_widget_text(widget_names.SPECTRUM_MEASURE_F_START_UNIT, "Hz")
    controller.set_widget_text(widget_names.SPECTRUM_MEASURE_F_STOP_UNIT, "Hz")
    controller.set_widget_text(widget_names.SPECTRUM_MEASURE_F_STEP_UNIT, "Hz")
    controller.set_widget_text(widget_names.SPECTRUM_MEASURE_GAIN, gain)
    controller.set_widget_text(widget_names.SPECTRUM_MEASURE_F_START, f_start)
    controller.set_widget_text(widget_names.SPECTRUM_MEASURE_F_STOP, f_stop)
    controller.set_widget_text(widget_names.SPECTRUM_MEASURE_F_STEP, f_step)
    controller.set_widget_text(widget_names.SPECTRUM_MEASURE_T_ON_TIME, t_on)
    controller.set_widget_text(widget_names.SPECTRUM_MEASURE_T_ON_UNIT, "ms")
    controller.set_widget_text(widget_names.SPECTRUM_MEASURE_T_OFF_TIME, t_off)
    controller.set_widget_text(widget_names.SPECTRUM_MEASURE_T_OFF_UNIT, "ms")
    controller.set_widget_text(widget_names.SPECTRUM_MEASURE_T_OFFSET_TIME, t_offset)
    controller.set_widget_text(widget_names.SPECTRUM_MEASURE_T_OFFSET_UNIT, "ms")


def fill_out_experiment_data():
    controller = GuiController()
    controller.set_widget_text(widget_names.EXPERIMENT_DATA_EXPERIMENT_NAME, "some experiment")
    controller.set_widget_text(widget_names.EXPERIMENT_DATA_TRANSDUCER_ID, "transducer007")
    controller.set_widget_text(widget_names.EXPERIMENT_DATA_MEDIUM, "water")
    controller.set_widget_text(widget_names.EXPERIMENT_DATA_ADD_ON_ID, "none")
    controller.set_widget_text(widget_names.EXPERIMENT_DATA_AUTHORS, "J. R. R. Tolkien")
    controller.set_widget_text(widget_names.EXPERIMENT_DATA_CONNECTOR_TYPE, "love")
    controller.set_widget_text(widget_names.EXPERIMENT_DATA_DESCRIPTION, "We are doing some serious sketchy stuff here")


async def start_ramp_procedure():
    set_ramp_args(**_get_ramp_test_args())

    controller = GuiController()
    controller.clear_text_changed_flag_of_widget(widget_names.PROC_CONTROLLING_RUNNING_PROC_LABEL)
    controller.clear_text_changed_flag_of_widget(widget_names.STATUS_BAR_PROCEDURE_LABEL)
    controller.press_button(widget_names.PROC_CONTROLLING_START_BUTTON)
    await controller.execute_events_until_idle()
    await proceed_without_experiment()

    proc_running_label, status_label = await asyncio.gather(
        controller.wait_for_widget_text(
            widget_names.PROC_CONTROLLING_RUNNING_PROC_LABEL,
            lambda current_text: "ramp" in current_text.lower(),
            10.0,
        ),
        controller.wait_for_widget_text(
            widget_names.STATUS_BAR_PROCEDURE_LABEL,
            lambda current_text: "ramp" in current_text.lower(),
            10.0,
        ),
    )
    assert "ramp" in proc_running_label.lower()
    assert "ramp" in status_label.lower()
    
    controller.clear_text_changed_flag_of_widget(widget_names.PROC_CONTROLLING_RUNNING_PROC_LABEL)
    controller.clear_text_changed_flag_of_widget(widget_names.STATUS_BAR_PROCEDURE_LABEL)


async def start_ramp_capture():
    controller = GuiController()
    controller.switch_to_tab(widget_names.MEASURING_TAB)
    controller.switch_to_tab(widget_names.PROCEDURES_TAB)

    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)
    fill_out_experiment_data()
    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)
    controller.set_widget_text(widget_names.MEASURING_TARGET_COMBOBOX, "Procedure")
    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)

    set_ramp_args(**_get_ramp_test_args())
    await controller.execute_events_until_idle()
    controller.clear_text_changed_flag_of_widget(widget_names.MEASURING_CONTROL_BUTTON)
    controller.clear_text_changed_flag_of_widget(widget_names.STATUS_BAR_PROCEDURE_LABEL)
    
    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)

    proc_label, label_control_button = await asyncio.gather(
        controller.wait_for_widget_text(
            widget_names.STATUS_BAR_PROCEDURE_LABEL,
            lambda current_text: "ramp" in current_text.lower(),
            10.0,
        ),
        controller.wait_for_widget_text_to_equal(
            widget_names.MEASURING_CONTROL_BUTTON,
            ui_labels.END_CAPTURE,
            10.0,
        ),
    )
    assert "ramp" in proc_label.lower()
    assert label_control_button == ui_labels.END_CAPTURE


async def start_spectrum_measure_capture(
    *,
    gain: str = "50",
    f_start: str = "100000",
    f_stop: str = "110000",
    f_step: str = "1000",
    t_on: str = "1000",
    t_off: str = "0",
    t_offset: str = "0",
):
    controller = GuiController()
    controller.switch_to_tab(widget_names.MEASURING_TAB)
    controller.switch_to_tab(widget_names.SPECTRUM_MEASURE_TAB)

    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)
    fill_out_experiment_data()
    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)
    controller.set_widget_text(widget_names.MEASURING_TARGET_COMBOBOX, "Spectrum Measure")
    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)

    set_spectrum_measure_args(
        gain=gain,
        f_start=f_start,
        f_stop=f_stop,
        f_step=f_step,
        t_on=t_on,
        t_off=t_off,
        t_offset=t_offset,
    )
    await controller.execute_events_until_idle()
    controller.clear_text_changed_flag_of_widget(widget_names.MEASURING_CONTROL_BUTTON)
    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)
    label_control_button = await controller.wait_for_widget_text_to_equal(
        widget_names.MEASURING_CONTROL_BUTTON,
        ui_labels.END_CAPTURE,
        timeout_s=2.0,
    )

    assert label_control_button == ui_labels.END_CAPTURE


async def postman_wait_for_worker_to_be_connected(timeout_s=15.0):
    controller = GuiController()

    status_widget_name = widget_names.widget_of_window(widget_names.POSTMAN, widget_names.WORKER_CONNECTION_STATUS)
    await controller.wait_for_widget_to_be_registered(status_widget_name, timeout_s)
    controller.clear_text_changed_flag_of_widget(status_widget_name)
    status = controller.get_widget_text(status_widget_name)
    if status == ui_labels.CONNECTED_TO_WORKER:
        return
        
    status = await controller.wait_for_widget_text_to_equal(status_widget_name, ui_labels.CONNECTED_TO_WORKER, timeout_s)
    assert status == ui_labels.CONNECTED_TO_WORKER, "Postman not connected to worker"
