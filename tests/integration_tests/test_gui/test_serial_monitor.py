from soniccontrol_gui.utils.testing import widget_names
from soniccontrol_gui.utils.testing.gui_controller import GuiController
import pytest

from soniccontrol_gui.utils.testing.workflows import send_over_serial_monitor


@pytest.mark.asyncio(loop_scope="package")
async def test_set_gain_over_serial_updates_status_bar():
    controller = GuiController()
    await send_over_serial_monitor("!gain=50")
    text = await controller.wait_for_widget_to_change_text(widget_names.STATUS_BAR_GAIN_LABEL, 1.0)
    assert "50 %" in text, f"Expected the gain to be 50 %, but the label is set to {text}"


@pytest.mark.asyncio(loop_scope="package")
async def test_sending_a_command_displays_it_in_the_monitor():
    controller = GuiController()
    command = "?info"
    await send_over_serial_monitor(command)
    command_entry = controller.get_text_of_widget_child(widget_names.SERIAL_MONITOR_SCROLL_FRAME, -2)
    assert command in command_entry, f"The command '{command}' is not part of the serial monitor output '{command_entry}'"

