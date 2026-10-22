import asyncio

import pytest
import pytest_asyncio

from soniccontrol import DeviceType
from sonic_pytest.device_setup import reset_at1_config_over_device
from sonic_pytest.gui import widget_names
from sonic_pytest.gui.gui_controller import GuiController
from sonic_pytest.gui.workflows import send_over_serial_monitor


def set_configuration_at1_values(atf: str, atk: str, att: str) -> None:
    controller = GuiController()
    controller.set_widget_text(widget_names.CONFIGURATION_AT_CONFIG_1_ATF_ENTRY_UNIT, "Hz")
    controller.set_widget_text(widget_names.CONFIGURATION_AT_CONFIG_1_ATT_ENTRY_UNIT, "C°")
    controller.set_widget_text(widget_names.CONFIGURATION_AT_CONFIG_1_ATF_ENTRY, atf)
    controller.set_widget_text(widget_names.CONFIGURATION_AT_CONFIG_1_ATK_ENTRY, atk)
    controller.set_widget_text(widget_names.CONFIGURATION_AT_CONFIG_1_ATT_ENTRY, att)

@pytest.mark.allowed_devices(DeviceType.MVP_WORKER)
@pytest_asyncio.fixture(scope="function", loop_scope="package", autouse=True)
async def configuration_tab_fixture(device_window):
    controller = GuiController()

    device = device_window.device
    assert device is not None

    await reset_at1_config_over_device(device)
    answer_atf = await send_over_serial_monitor("?atf1")
    answer_att = await send_over_serial_monitor("?att1")
    answer_atk = await send_over_serial_monitor("?atk1")
    assert "0" in answer_atf, f"Expected reset ?atf1 answer to contain 0, got '{answer_atf}'"
    assert "0" in answer_att, f"Expected reset ?att1 answer to contain 0, got '{answer_att}'"
    assert "0" in answer_atk, f"Expected reset ?atk1 answer to contain 0, got '{answer_atk}'"

    controller.switch_to_tab(widget_names.CONFIGURATION_TAB)

    set_configuration_at1_values("0", "0", "0.0")
    controller.set_widget_text(widget_names.CONFIGURATION_BROWSE_FILES_ENTRY, "")

    controller.clear_text_changed_flags()
    yield
    controller.clear_text_changed_flags()


@pytest.mark.allowed_devices(DeviceType.MVP_WORKER)
@pytest.mark.asyncio(loop_scope="package")
async def test_send_atf_configs_to_device():
    controller = GuiController()

    set_configuration_at1_values("200000", "10", "21.0")
    controller.press_button(widget_names.CONFIGURATION_SUBMIT_CONFIG_BUTTON)
    await controller.wait_for_pending_actions(20.0)

    controller.switch_to_tab(widget_names.SERIAL_MONITOR_TAB)
    answer_atf = await send_over_serial_monitor("?atf1")
    assert "200000" in answer_atf, f"Expected '200000', but got '{answer_atf}'"

    answer_atk = await send_over_serial_monitor("?atk1")
    assert "10" in answer_atk, f"Expected '10', but got '{answer_atk}'"

    answer_att = await send_over_serial_monitor("?att1")
    assert "21" in answer_att, f"Expected '21', but got '{answer_att}'"


@pytest.mark.allowed_devices(DeviceType.MVP_WORKER)
@pytest.mark.asyncio(loop_scope="package")
async def test_configure_device_with_init_script(tmp_path):
    controller = GuiController()
    controller.clear_text_changed_flags()

    init_script_path = tmp_path / "init_script_test.sonic"
    init_script_content = """frequency 690420\ngain 10\n"""
    init_script_path.write_text(init_script_content)

    controller.set_widget_text(widget_names.CONFIGURATION_BROWSE_FILES_ENTRY, str(init_script_path.resolve()))
    controller.press_button(widget_names.CONFIGURATION_SUBMIT_CONFIG_BUTTON)

    gain_label, freq_label = await asyncio.gather(
        controller.wait_for_widget_text_to_contain(widget_names.STATUS_BAR_GAIN_LABEL, "10 %", 20.0),
        controller.wait_for_widget_text_to_contain(widget_names.STATUS_BAR_FREQ_LABEL, "690420 Hz", 20.0),
    )

    assert "690420 Hz" in freq_label, f"Expected 'Frequency: 690420 Hz', but got '{freq_label}'"
    assert "10 %" in gain_label, f"Expected 'Gain: 10 %', but got '{gain_label}'"
