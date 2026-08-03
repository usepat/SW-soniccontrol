import pytest
import pytest_asyncio

from sonic_protocol.schema import Loglevel, Signal, SIPrefix
from soniccontrol.procedures.procedure import ProcedureType
from sonic_pytest.remote_controller.asserts import assert_answer, send_command_and_check_response
from soniccontrol import EFieldName, Procedure, RamperArgs, WipeArgs, commands, DeviceType
import asyncio


async def setup_valid_ramp_args(remote_controller, args: RamperArgs | None = None) -> RamperArgs:
    ramp_args = RamperArgs() if args is None else args
    await send_command_and_check_response(
        remote_controller,
        commands.SetRampFStart(int(ramp_args.f_start.to_prefix(SIPrefix.NONE))),
    )
    await send_command_and_check_response(
        remote_controller,
        commands.SetRampFStop(int(ramp_args.f_stop.to_prefix(SIPrefix.NONE))),
    )
    await send_command_and_check_response(
        remote_controller,
        commands.SetRampFStep(int(ramp_args.f_step.to_prefix(SIPrefix.NONE))),
    )
    await send_command_and_check_response(
        remote_controller,
        commands.SetRampTOn(int(ramp_args.t_on.duration_in_ms)),
    )
    await send_command_and_check_response(
        remote_controller,
        commands.SetRampTOff(int(ramp_args.t_off.duration_in_ms)),
    )
    await send_command_and_check_response(
        remote_controller,
        commands.SetRampGain(int(ramp_args.gain.to_prefix(SIPrefix.NONE))),
    )
    return ramp_args


async def setup_valid_wipe_args(remote_controller, args: WipeArgs | None = None) -> WipeArgs:
    wipe_args = WipeArgs() if args is None else args
    await send_command_and_check_response(
        remote_controller,
        commands.SetWipeFRange(int(wipe_args.f_range.to_prefix(SIPrefix.NONE))),
    )
    await send_command_and_check_response(
        remote_controller,
        commands.SetWipeFStep(int(wipe_args.f_step.to_prefix(SIPrefix.NONE))),
    )
    await send_command_and_check_response(
        remote_controller,
        commands.SetWipeTOn(int(wipe_args.t_on.duration_in_ms)),
    )
    await send_command_and_check_response(
        remote_controller,
        commands.SetWipeTOff(int(wipe_args.t_off.duration_in_ms)),
    )
    await send_command_and_check_response(
        remote_controller,
        commands.SetWipeTPause(int(wipe_args.t_pause.duration_in_ms)),
    )
    await send_command_and_check_response(
        remote_controller,
        commands.SetWipeGain(int(wipe_args.gain.to_prefix(SIPrefix.NONE))),
    )
    return wipe_args


async def setup_valid_at_configs(remote_controller) -> None:
    atf_values = [500000, 1000000, 3000000, 4000000]

    for index, atf_value in enumerate(atf_values, start=1):
        await send_command_and_check_response(
            remote_controller,
            commands.SetAtf(index, atf_value),
        )
        await send_command_and_check_response(
            remote_controller,
            commands.SetAtk(index, 0),
        )
        await send_command_and_check_response(
            remote_controller,
            commands.SetAtt(index, 0),
        )


@pytest_asyncio.fixture(autouse=True, scope="function", loop_scope="package")
async def setup_procedures(request, remote_controller):
    # Here we check for each test, it can be execute 
    # by checking if the given procedure is enabled by the skip_if_proc_not_enabled marker

    for mark in request.node.iter_markers(name="skip_if_proc_not_enabled"):
        if not mark.args:
            raise ValueError("skip_if_proc_not_enabled requires a Procedure argument")
        
        proc: ProcedureType = mark.args[0]
        proc_enabled = remote_controller.is_procedure_enabled(proc)

        if not proc_enabled:
            pytest.skip(f"The device has not the procedure {proc.name} enabled")

    # even if the procedures are not enabled, setting attributes of them works always
    # so no checks needed here
    await setup_valid_at_configs(remote_controller)
    await setup_valid_ramp_args(remote_controller)
    await setup_valid_wipe_args(remote_controller)

    yield

    await send_command_and_check_response(remote_controller, commands.SetStop(), raise_exception = False, check_command_not_permitted=True)


@pytest_asyncio.fixture(scope="function", loop_scope="package")
async def disable_procedure_logger(remote_controller):
    if not remote_controller._device._uses_modbus():
        
        await send_command_and_check_response(remote_controller, commands.SetLogLevel("procedureLogger", Loglevel.DISABLED))

    yield
    if not remote_controller._device._uses_modbus():
        await send_command_and_check_response(remote_controller, commands.SetLogLevel("procedureLogger", Loglevel.ERROR))


@pytest.mark.skip_if_proc_not_enabled(ProcedureType.RAMP)
@pytest.mark.asyncio(loop_scope="package")
async def test_procedure_returns_error_if_f_start_and_f_stop_are_the_same(remote_controller):
    val = 100100
    await send_command_and_check_response(remote_controller, commands.SetRampFStart(val))
    await send_command_and_check_response(remote_controller, commands.SetRampFStop(val))

    answer = await remote_controller.send_command(commands.SetRamp())
    assert not answer.valid, "Expected answer to be false, because f_start and f_stop are the same"


@pytest.mark.allowed_devices(DeviceType.MVP_WORKER, DeviceType.POSTMAN)
@pytest.mark.skip_if_proc_not_enabled(ProcedureType.RAMP)
@pytest.mark.asyncio(loop_scope="package")
async def test_setter_commands_get_blocked_during_procedure_run(remote_controller):
    answer = await remote_controller.send_command(commands.SetRamp())
    assert_answer(answer, {EFieldName.PROCEDURE: Procedure.RAMP})

    answer = await remote_controller.send_command(commands.SetFrequency(200000))
    assert not answer.valid, "Expected set_freq to fail, while a procedure is running"


@pytest.mark.allowed_devices(DeviceType.MVP_WORKER, DeviceType.POSTMAN)
@pytest.mark.skip_if_proc_not_enabled(ProcedureType.RAMP)
@pytest.mark.asyncio(loop_scope="package")
async def test_getter_commands_are_allowed_during_procedure_run(remote_controller):
    
    answer = await remote_controller.send_command(commands.SetRamp())
    assert_answer(answer, {EFieldName.PROCEDURE: Procedure.RAMP})

    answer = await remote_controller.send_command(commands.GetFreq())
    assert answer.valid, "Expected get_freq to succeed, while a procedure is running"


@pytest.mark.allowed_devices(DeviceType.MVP_WORKER, DeviceType.POSTMAN)
@pytest.mark.skip_if_proc_not_enabled(ProcedureType.RAMP)
@pytest.mark.asyncio(loop_scope="package")
async def test_stop_turns_off_procedure(remote_controller, disable_procedure_logger):
    await send_command_and_check_response(remote_controller, commands.SetRamp())
    assert_answer(await remote_controller.get_update(), {EFieldName.PROCEDURE: Procedure.RAMP})

    await send_command_and_check_response(remote_controller, commands.SetStop(), check_command_not_permitted=True)
    assert_answer(await remote_controller.get_update(), {EFieldName.PROCEDURE: Procedure.NO_PROC})


@pytest.mark.allowed_devices(DeviceType.MVP_WORKER, DeviceType.POSTMAN)
@pytest.mark.skip_if_proc_not_enabled(ProcedureType.RAMP)
@pytest.mark.asyncio(loop_scope="package")
async def test_if_ramp_resets_running_proc_and_signal(remote_controller, disable_procedure_logger):
    await send_command_and_check_response(remote_controller, commands.SetRamp())

    await asyncio.sleep(12) # ramp needs 12 seconds to execute
    answer = await remote_controller.get_update()
    assert_answer(answer, {EFieldName.PROCEDURE: Procedure.NO_PROC, EFieldName.SIGNAL: Signal.OFF})


@pytest.mark.allowed_devices(DeviceType.MVP_WORKER, DeviceType.POSTMAN)
@pytest.mark.skip_if_proc_not_enabled(ProcedureType.WIPE)
@pytest.mark.asyncio(loop_scope="package")
async def test_if_wipe_does_not_crash(remote_controller, disable_procedure_logger):
    await send_command_and_check_response(remote_controller, commands.SetWipe())

    for _ in range(10):
        await asyncio.sleep(2)
        answer = await remote_controller.get_update()
        assert_answer(answer, {EFieldName.PROCEDURE: Procedure.WIPE})
