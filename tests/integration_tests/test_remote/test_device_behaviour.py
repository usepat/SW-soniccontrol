import pytest

from .asserts import assert_answer, send_command_and_check_response
from soniccontrol import EFieldName, commands, DeviceType
from sonic_protocol.schema import ControlMode


@pytest.mark.asyncio(loop_scope="package")
async def test_if_devices_saves_transducer_state(remote_controller):
    gain = 96
    await send_command_and_check_response(remote_controller, commands.SetGain(gain))

    await remote_controller.restart()
    await remote_controller.stop_running_processes()

    answer = await remote_controller.get_update()
    assert_answer(answer, { EFieldName.GAIN: gain })


@pytest.mark.allowed_devices(DeviceType.DESCALE)
@pytest.mark.asyncio(loop_scope="package")
async def test_if_input_source_can_be_set_if_analog_is_set(remote_controller):
    answer = await remote_controller.send_command("!control_mode=analog")
    assert_answer(answer, {EFieldName.COMM_MODE: ControlMode.ANALOG })
    answer = await remote_controller.send_command("!control_mode=remote")
    assert_answer(answer, {EFieldName.COMM_MODE: ControlMode.REMOTE })

