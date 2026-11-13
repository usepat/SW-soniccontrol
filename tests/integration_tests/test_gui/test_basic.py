from sonic_pytest.gui import widget_names
from sonic_pytest.gui.gui_controller import GuiController
import pytest
from soniccontrol import DeviceType
from soniccontrol_gui.constants import ui_labels

@pytest.mark.allowed_devices(DeviceType.MVP_WORKER, DeviceType.CRYSTAL, DeviceType.POSTMAN)
@pytest.mark.asyncio(loop_scope="package")
async def test_set_frequency_over_home_tab():
    controller = GuiController()
    controller.switch_to_tab(widget_names.HOME_TAB)
    freq = "201000"
    controller.set_widget_text(widget_names.HOME_FREQUENCY_ENTRY_UNIT, "Hz")
    controller.set_widget_text(widget_names.HOME_FREQUENCY_ENTRY, freq)
    if controller.get_widget_text(widget_names.HOME_AUTO_SEND_BUTTON) == ui_labels.MANUAL_SEND_LABEL:
        controller.press_button(widget_names.HOME_AUTO_SEND_BUTTON)
    await controller.wait_for_widget_text_to_contain(widget_names.HOME_AUTO_SEND_BUTTON, ui_labels.AUTO_SEND_LABEL, 1.0)
    controller.press_button(widget_names.HOME_SEND_BUTTON)
    text = await controller.wait_for_widget_text_to_contain(widget_names.STATUS_BAR_FREQ_LABEL, freq, 5.0)
    assert freq in text, f"Expected the frequency to be {freq}, but the label is set to {text}"
