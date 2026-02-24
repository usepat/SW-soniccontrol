import asyncio
from soniccontrol_gui.utils.testing import widget_names
from soniccontrol_gui.utils.testing.gui_controller import GuiController
import pytest
import pytest_asyncio
from soniccontrol_gui.constants import ui_labels
from soniccontrol_gui.utils.testing.workflows import proceed_without_experiment

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


@pytest.mark.asyncio(loop_scope="package")
async def test_execute_script_holds_application():
    controller = GuiController()
    controller.set_widget_text(widget_names.EDITOR_TEXT_EDITOR, 
    """
    send "!ON"
    hold 5s
    send "!OFF"
    """)
    controller.press_button(widget_names.EDITOR_START_PAUSE_CONTINUE_BUTTON)

    # Message box appears if script is started without experiment
    await proceed_without_experiment()
    
    await asyncio.sleep(4)
    text_signal_after_4s = controller.get_widget_text(widget_names.STATUS_BAR_SIGNAL_LABEL)
    await asyncio.sleep(2)
    text_signal_after_6s = controller.get_widget_text(widget_names.STATUS_BAR_SIGNAL_LABEL)
    
    assert "on" in text_signal_after_4s, "Expected signal to be turned on"
    assert "off" in text_signal_after_6s, "Expected signal to be turned off"

