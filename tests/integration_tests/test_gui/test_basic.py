from soniccontrol_gui.utils.testing import widget_names
from soniccontrol_gui.utils.testing.gui_controller import GuiController
import pytest
from soniccontrol import DeviceType

@pytest.mark.allowed_devices(DeviceType.MVP_WORKER, DeviceType.CRYSTAL, DeviceType.POSTMAN)
@pytest.mark.asyncio(loop_scope="package")
async def test_set_frequency_over_home_tab():
    controller = GuiController()
    controller.switch_to_tab(widget_names.HOME_TAB)

    freq = "201000"
    controller.set_widget_text(widget_names.HOME_FREQUENCY_ENTRY, freq)
    controller.press_button(widget_names.HOME_SEND_BUTTON)
    text = await controller.wait_for_widget_to_change_text(widget_names.STATUS_BAR_FREQ_LABEL, 1.0)
    assert freq in text, f"Expected the frequency to be {freq}, but the label is set to {text}"
