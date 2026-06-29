from sonic_pytest.gui import widget_names
from sonic_pytest.gui.gui_controller import GuiController
import pytest
import pytest_asyncio
from soniccontrol_gui.constants import ui_labels
from sonic_pytest.gui.workflows import proceed_without_experiment, send_over_serial_monitor

@pytest_asyncio.fixture(scope="function", loop_scope="package", autouse=True)
async def scripting_tab_fixture():
    controller = GuiController()
    controller.switch_to_tab(widget_names.SCRIPTING_TAB)

    yield

    text_button = controller.get_widget_text(widget_names.EDITOR_START_PAUSE_CONTINUE_BUTTON)
    if text_button != ui_labels.START_LABEL:
        controller.press_button(widget_names.EDITOR_STOP_BUTTON)
    
    controller.set_widget_text(widget_names.EDITOR_TEXT_EDITOR, "")
    await controller.execute_events_until_idle()

@pytest.mark.skip_if_modbus_enabled()
@pytest.mark.asyncio(loop_scope="package")
async def test_execute_script_holds_application():
    controller = GuiController()
    await send_over_serial_monitor("!sonic_force")
    await send_over_serial_monitor("!OFF")
    await controller.wait_for_widget_text_to_contain(widget_names.STATUS_BAR_SIGNAL_LABEL, "off", 5.0)
    controller.switch_to_tab(widget_names.SCRIPTING_TAB)

    controller.set_widget_text(widget_names.EDITOR_TEXT_EDITOR, 
    """
    hold 2s
    send "!ON"
    hold 5s
    send "!OFF"
    """
    )
    controller.press_button(widget_names.EDITOR_START_PAUSE_CONTINUE_BUTTON)

    # Message box appears if script is started without experiment
    await proceed_without_experiment()

    await controller.wait_for_widget_text(
        widget_names.EDITOR_START_PAUSE_CONTINUE_BUTTON,
        lambda text: text == ui_labels.PAUSE_LABEL,
        5.0,
    )

    text_signal_after_4s = await controller.wait_for_widget_text_to_contain(widget_names.STATUS_BAR_SIGNAL_LABEL, "on", 8.0)
    text_signal_after_6s = await controller.wait_for_widget_text_to_contain(widget_names.STATUS_BAR_SIGNAL_LABEL, "off", 8.0)
    
    assert "on" in text_signal_after_4s, "Expected signal to be turned on"
    assert "off" in text_signal_after_6s, "Expected signal to be turned off"

