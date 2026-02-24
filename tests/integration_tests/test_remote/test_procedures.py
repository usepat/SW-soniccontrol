import pytest
import pytest_asyncio

from sonic_protocol.schema import Loglevel, Signal
from .asserts import assert_answer, send_command_and_check_response
from soniccontrol import EFieldName, Procedure, commands, Procedure, DeviceType
import asyncio


@pytest_asyncio.fixture(autouse=True, scope="function", loop_scope="package")
async def setup_procedures(remote_controller):
    await send_command_and_check_response(remote_controller, commands.SetRampFStart(100000))
    await send_command_and_check_response(remote_controller, commands.SetRampFStop(150000))
    await send_command_and_check_response(remote_controller, commands.SetRampFStep(10000))
    await send_command_and_check_response(remote_controller, commands.SetRampTOn(2000))
    await send_command_and_check_response(remote_controller, commands.SetRampTOff(0))
    await send_command_and_check_response(remote_controller, commands.SetRampGain(100))

    yield

    await remote_controller.send_command(commands.SetStop())

@pytest_asyncio.fixture(scope="function", loop_scope="package")
async def disable_procedure_logger(remote_controller):
    await remote_controller.send_command(commands.SetLogLevel("procedureLogger", Loglevel.DISABLED))

    yield

    await remote_controller.send_command(commands.SetLogLevel("procedureLogger", Loglevel.ERROR))


@pytest.mark.allowed_devices(DeviceType.MVP_WORKER, DeviceType.POSTMAN)
@pytest.mark.asyncio(loop_scope="package")
async def test_procedure_returns_error_if_f_start_and_f_stop_are_the_same(remote_controller):
    val = 100100
    await send_command_and_check_response(remote_controller, commands.SetRampFStart(val))
    await send_command_and_check_response(remote_controller, commands.SetRampFStop(val))

    answer = await remote_controller.send_command(commands.SetRamp())
    assert not answer.valid, "Expected answer to be false, because f_start and f_stop are the same"


@pytest.mark.allowed_devices(DeviceType.MVP_WORKER, DeviceType.POSTMAN)
@pytest.mark.asyncio(loop_scope="package")
async def test_setter_commands_get_blocked_during_procedure_run(remote_controller):
    answer = await remote_controller.send_command(commands.SetRamp())
    assert_answer(answer, {EFieldName.PROCEDURE: Procedure.RAMP})

    answer = await remote_controller.send_command(commands.SetFrequency(200000))
    assert not answer.valid, "Expected set_freq to fail, while a procedure is running"


@pytest.mark.allowed_devices(DeviceType.MVP_WORKER, DeviceType.POSTMAN)
@pytest.mark.asyncio(loop_scope="package")
async def test_getter_commands_are_allowed_during_procedure_run(remote_controller):
    answer = await remote_controller.send_command(commands.SetRamp())
    assert_answer(answer, {EFieldName.PROCEDURE: Procedure.RAMP})

    answer = await remote_controller.send_command(commands.GetFreq())
    assert answer.valid, "Expected get_freq to succeed, while a procedure is running"


@pytest.mark.allowed_devices(DeviceType.MVP_WORKER, DeviceType.POSTMAN)
@pytest.mark.asyncio(loop_scope="package")
async def test_stop_turns_off_procedure(remote_controller, disable_procedure_logger):
    await send_command_and_check_response(remote_controller, commands.SetRamp())
    assert_answer(await remote_controller.send_command(commands.GetUpdate()), {EFieldName.PROCEDURE: Procedure.RAMP})

    await send_command_and_check_response(remote_controller, commands.SetStop())
    assert_answer(await remote_controller.send_command(commands.GetUpdate()), {EFieldName.PROCEDURE: Procedure.NO_PROC})


@pytest.mark.allowed_devices(DeviceType.MVP_WORKER, DeviceType.POSTMAN)
@pytest.mark.asyncio(loop_scope="package")
async def test_if_ramp_resets_running_proc_and_signal(remote_controller, disable_procedure_logger):
    await send_command_and_check_response(remote_controller, commands.SetRamp())

    await asyncio.sleep(12) # ramp needs 12 seconds to execute
    answer = await remote_controller.send_command(commands.GetUpdate())
    assert_answer(answer, {EFieldName.PROCEDURE: Procedure.NO_PROC, EFieldName.SIGNAL: Signal.OFF})
