import pytest
import asyncio
from soniccontrol_gui.utils.testing import widget_names
from soniccontrol_gui.utils.testing.gui_controller import GuiController
from soniccontrol_gui.constants import ui_labels
from soniccontrol_gui.utils.testing.workflows import send_over_serial_monitor
import pytest_asyncio
from soniccontrol import DeviceType


@pytest_asyncio.fixture(scope="function", loop_scope="package", autouse=True)
async def configuration_tab_fixture():
    controller = GuiController()

    await send_over_serial_monitor("!atf1=0")
    await send_over_serial_monitor("!att1=0")
    await send_over_serial_monitor("!atk1=0")

    controller.switch_to_tab(widget_names.CONFIGURATION_TAB)

    controller.set_widget_text(widget_names.CONFIGURATION_AT_CONFIG_1_ATF_ENTRY, "0")
    controller.set_widget_text(widget_names.CONFIGURATION_AT_CONFIG_1_ATK_ENTRY, "0")
    controller.set_widget_text(widget_names.CONFIGURATION_AT_CONFIG_1_ATT_ENTRY, "0.0")
    controller.set_widget_text(widget_names.CONFIGURATION_BROWSE_FILES_ENTRY, "")

    controller.clear_text_changed_flags()
    yield
    controller.clear_text_changed_flags()


@pytest.mark.allowed_devices(DeviceType.MVP_WORKER)
@pytest.mark.asyncio(loop_scope="package")
async def test_send_atf_configs_to_device():
    controller = GuiController()

    controller.set_widget_text(widget_names.CONFIGURATION_AT_CONFIG_1_ATF_ENTRY, "200000")
    controller.set_widget_text(widget_names.CONFIGURATION_AT_CONFIG_1_ATK_ENTRY, "10")
    controller.set_widget_text(widget_names.CONFIGURATION_AT_CONFIG_1_ATT_ENTRY, "21.0")
    controller.press_button(widget_names.CONFIGURATION_SUBMIT_CONFIG_BUTTON)
    await asyncio.sleep(5)

    controller.switch_to_tab(widget_names.SERIAL_MONITOR_TAB)
    answer_atf = await send_over_serial_monitor("?atf1")
    assert "200000 Hz" in answer_atf, f"Expected '200000 Hz', but got '{answer_atf}'"

    answer_atk = await send_over_serial_monitor("?atk1")
    assert "10" in answer_atk, f"Expected '10', but got '{answer_atk}'"

    answer_att = await send_over_serial_monitor("?att1")
    assert "21" in answer_att, f"Expected '21', but got '{answer_att}'"


@pytest.mark.asyncio(loop_scope="package")
async def test_configure_device_with_init_script(tmp_path):
    controller = GuiController()

    init_script_path = tmp_path / "init_script_test.sonic"
    init_script_content = """frequency 690420\ngain 10\n"""
    init_script_path.write_text(init_script_content)

    controller.set_widget_text(widget_names.CONFIGURATION_BROWSE_FILES_ENTRY, str(init_script_path.resolve()))
    controller.press_button(widget_names.CONFIGURATION_SUBMIT_CONFIG_BUTTON)
    
    labels_status_bar = [
        widget_names.STATUS_BAR_GAIN_LABEL,
        widget_names.STATUS_BAR_FREQ_LABEL
    ]
    gain_label, freq_label = await controller.wait_for_multiple_widgets_to_change_text(*labels_status_bar, timeout_s=20.0)

    assert "690420 Hz" in freq_label, f"Expected 'Frequency: 690420 Hz', but got '{freq_label}'"
    assert "10 %" in gain_label, f"Expected 'Gain: 10 %', but got '{gain_label}'"
