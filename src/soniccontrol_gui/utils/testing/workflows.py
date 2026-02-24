import asyncio
from soniccontrol_gui.utils.testing import widget_names
from soniccontrol_gui.utils.testing.gui_controller import GuiController
from soniccontrol_gui.constants import ui_labels

async def send_over_serial_monitor(command: str) -> str:
    controller = GuiController()
    controller.switch_to_tab(widget_names.SERIAL_MONITOR_TAB)
    controller.set_widget_text(widget_names.SERIAL_MONITOR_COMMAND_LINE_INPUT_ENTRY, command)
    controller.press_button(widget_names.SERIAL_MONITOR_SEND_BUTTON)
    await controller.execute_events_until_idle()

    max_iter = 10
    for _ in range(max_iter):
        answer = controller.get_text_of_widget_child(widget_names.SERIAL_MONITOR_SCROLL_FRAME, -1)
        if not answer.startswith(">>>"):
            # commands are always proceeded with '>>>', answers never
            return answer
        
        await controller.execute_events_until_idle()
        await asyncio.sleep(0.1)
    
    raise AssertionError("No answer could be received")


async def proceed_without_experiment():
    controller = GuiController()
    await controller.wait_for_widget_to_be_registered(widget_names.MESSAGE_BOX, 0.2)
    controller.press_button(widget_names.MESSAGE_BOX_OPTION_PROCEED)


def set_ramp_args():
    controller = GuiController()
    controller.set_widget_text(widget_names.RAMP_F_START, "100000")
    controller.set_widget_text(widget_names.RAMP_F_STOP, "200000")
    controller.set_widget_text(widget_names.RAMP_F_STEP, "10000")
    controller.set_widget_text(widget_names.RAMP_T_ON_TIME, "1000")
    controller.set_widget_text(widget_names.RAMP_T_ON_UNIT, "ms")
    controller.set_widget_text(widget_names.RAMP_T_OFF_TIME, "1000")
    controller.set_widget_text(widget_names.RAMP_T_OFF_UNIT, "ms")
    controller.set_widget_text(widget_names.RAMP_GAIN, "100")


def set_spectrum_measure_args():
    controller = GuiController()
    controller.set_widget_text(widget_names.SPECTRUM_MEASURE_GAIN, "50")
    controller.set_widget_text(widget_names.SPECTRUM_MEASURE_F_START, "100000")
    controller.set_widget_text(widget_names.SPECTRUM_MEASURE_F_STOP, "105000")
    controller.set_widget_text(widget_names.SPECTRUM_MEASURE_F_STEP, "1000")
    controller.set_widget_text(widget_names.SPECTRUM_MEASURE_T_ON_TIME, "250")
    controller.set_widget_text(widget_names.SPECTRUM_MEASURE_T_ON_UNIT, "ms")
    controller.set_widget_text(widget_names.SPECTRUM_MEASURE_T_OFF_TIME, "250")
    controller.set_widget_text(widget_names.SPECTRUM_MEASURE_T_OFF_UNIT, "ms")
    controller.set_widget_text(widget_names.SPECTRUM_MEASURE_T_OFFSET_TIME, "500")
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
    set_ramp_args()

    controller = GuiController()
    controller.clear_text_changed_flag_of_widget(widget_names.PROC_CONTROLLING_RUNNING_PROC_LABEL)
    controller.clear_text_changed_flag_of_widget(widget_names.STATUS_BAR_PROCEDURE_LABEL)
    controller.press_button(widget_names.PROC_CONTROLLING_START_BUTTON)
    await controller.execute_events_until_idle()
    await proceed_without_experiment()

    # We have to wait here for both labels to change text, because the proc running label is immediately set, 
    # then it configures the args and then it starts the procedure, only then the status bar label is updated
    await controller.wait_for_multiple_widgets_to_change_text(
        widget_names.PROC_CONTROLLING_RUNNING_PROC_LABEL, 
        widget_names.STATUS_BAR_PROCEDURE_LABEL,
        timeout_s=10.0
    )


async def start_ramp_capture():
    controller = GuiController()
    controller.switch_to_tab(widget_names.MEASURING_TAB)
    controller.switch_to_tab(widget_names.PROCEDURES_TAB)

    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)
    fill_out_experiment_data()
    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)
    controller.set_widget_text(widget_names.MEASURING_TARGET_COMBOBOX, "Procedure")
    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)

    set_ramp_args()
    await controller.execute_events_until_idle()
    controller.clear_text_changed_flag_of_widget(widget_names.MEASURING_CONTROL_BUTTON)
    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)

    proc_label, label_control_button = await controller.wait_for_multiple_widgets_to_change_text(
        widget_names.STATUS_BAR_PROCEDURE_LABEL, widget_names.MEASURING_CONTROL_BUTTON, 
        timeout_s=10.0
    )
    assert "ramp" in proc_label
    assert label_control_button == ui_labels.END_CAPTURE


async def start_spectrum_measure_capture():
    controller = GuiController()
    controller.switch_to_tab(widget_names.MEASURING_TAB)
    controller.switch_to_tab(widget_names.SPECTRUM_MEASURE_TAB)

    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)
    fill_out_experiment_data()
    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)
    controller.set_widget_text(widget_names.MEASURING_TARGET_COMBOBOX, "Spectrum Measure")
    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)

    set_spectrum_measure_args()
    await controller.execute_events_until_idle()
    controller.clear_text_changed_flag_of_widget(widget_names.MEASURING_CONTROL_BUTTON)
    controller.press_button(widget_names.MEASURING_CONTROL_BUTTON)

    label_control_button = await controller.wait_for_widget_to_change_text(
        widget_names.MEASURING_CONTROL_BUTTON, 
        timeout_s=2.0
    )

    assert label_control_button == ui_labels.END_CAPTURE
