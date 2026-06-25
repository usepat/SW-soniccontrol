from sonic_pytest.gui import widget_names
from sonic_pytest.gui.gui_controller import GuiController
import pytest

from sonic_pytest.gui.workflows import send_over_serial_monitor

@pytest.mark.asyncio(loop_scope="package")
async def test_set_gain_over_serial_updates_status_bar():
    controller = GuiController()
    await send_over_serial_monitor("!sonic_force")
    await send_over_serial_monitor("!gain=50")
    text = await controller.wait_for_widget_text_to_contain(widget_names.STATUS_BAR_GAIN_LABEL, "50 %", 5.0)
    assert "50 %" in text, f"Expected the gain to be 50 %, but the label is set to {text}"

@pytest.mark.asyncio(loop_scope="package")
async def test_sending_a_command_displays_it_in_the_monitor():
    controller = GuiController()
    command = "?info"
    existing_entries = controller.get_texts_of_widget_children(widget_names.SERIAL_MONITOR_SCROLL_FRAME)
    await send_over_serial_monitor(command)
    updated_entries = controller.get_texts_of_widget_children(widget_names.SERIAL_MONITOR_SCROLL_FRAME)
    new_entries = updated_entries[len(existing_entries):]
    command_entry = next((entry for entry in new_entries if command in entry), "")
    assert command in command_entry, f"The command '{command}' is not part of the serial monitor output '{command_entry}'"


# add test where monitor gets cleared and then used afterwards
