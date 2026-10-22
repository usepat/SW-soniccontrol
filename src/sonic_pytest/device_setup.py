from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from sonic_protocol.python_parser import commands
from sonic_protocol.schema import ControlMode, DeviceType, Loglevel

if TYPE_CHECKING:
    from soniccontrol import RemoteController
    from soniccontrol.sonic_device import SonicDevice


DEFAULT_TEST_SETUP_DEBUG_INDEX = 5
DEFAULT_PROCEDURE_SETUP_DEBUG_INDEX = 6
RESET_AT1_CONFIG_DEBUG_INDEX = 7


def _supports_debug_test(device: SonicDevice) -> bool:
    return device.has_command(commands.DebugTest(DEFAULT_TEST_SETUP_DEBUG_INDEX))


def _manual_setup_commands(device_type: DeviceType) -> list[tuple[str, bool]]:
    commands: list[tuple[str, bool]] = [
        ("!stop", True),
        ("!debug_test3", True),
        ("!clear_errors", True),
    ]

    if device_type == DeviceType.MVP_WORKER:
        commands.append(("!freq=100000", False))
    elif device_type == DeviceType.DESCALE:
        commands.append(("!swf=5", False))

    commands.extend([
        ("!gain=50", False),
        ("!OFF", False),
    ])
    return commands


def _raw_answer_is_success(answer: str) -> bool:
    try:
        command_code = int(answer.strip().split("#", 1)[0])
    except (IndexError, ValueError):
        return False

    return command_code < 20000


async def apply_default_test_setup_over_serial_monitor(
    device_type: DeviceType,
    send_command: Callable[[str, bool], Awaitable[str]],
) -> None:
    answer = await send_command(f"!debug_test{DEFAULT_TEST_SETUP_DEBUG_INDEX}", True)
    if _raw_answer_is_success(answer):
        return

    for command, allow_fail in _manual_setup_commands(device_type):
        await send_command(command, allow_fail)


async def apply_default_test_setup_over_device(device: SonicDevice) -> None:
    if _supports_debug_test(device):
        answer = await device.execute_command(
            commands.DebugTest(DEFAULT_TEST_SETUP_DEBUG_INDEX),
            raise_exception=False,
        )
        if answer.is_valid and not answer.is_error_msg:
            return

    await device.execute_command(commands.SetStop(), raise_exception=False)
    await device.execute_command(commands.DebugTest(3), raise_exception=False)
    await device.execute_command(commands.ClearErrors(), raise_exception=False)

    if device.info.device_type == DeviceType.MVP_WORKER:
        await device.execute_command(commands.SetFrequency(100_000))
    elif device.info.device_type == DeviceType.DESCALE:
        await device.execute_command(commands.SetSwf(5))

    await device.execute_command(commands.SetGain(50))
    await device.execute_command(commands.SetOff())


async def apply_default_test_setup_over_remote_controller(
    controller: RemoteController,
    device_type: DeviceType,
) -> None:
    if _supports_debug_test(controller.device):
        answer = await controller.send_command(
            commands.DebugTest(DEFAULT_TEST_SETUP_DEBUG_INDEX),
            raise_exception=False,
        )
        if answer.is_valid and not answer.is_error_msg:
            return

    for command, allow_fail in _manual_setup_commands(device_type):
        await controller.send_command(command, raise_exception=not allow_fail)


async def reset_remote_controller_test_state(remote_controller: RemoteController) -> None:
    if _supports_debug_test(remote_controller.device):
        answer = await remote_controller.send_command(
            commands.DebugTest(DEFAULT_TEST_SETUP_DEBUG_INDEX),
            raise_exception=False,
        )
        if answer.is_valid and not answer.is_error_msg:
            return

    if not remote_controller._device._uses_modbus():
        await remote_controller.send_command(commands.SetLogLevel("global", Loglevel.ERROR))

    await remote_controller.send_command(commands.SetControlMode(ControlMode.REMOTE))

    await remote_controller.send_command(commands.ClearErrors(), raise_exception=False)
    await remote_controller.send_command(commands.SonicForce())
    await remote_controller.send_command(commands.SetStop(), raise_exception=False)
    await remote_controller.send_command(commands.SetOff())


async def apply_default_procedure_setup_over_remote_controller(
    remote_controller: RemoteController,
) -> None:
    if _supports_debug_test(remote_controller.device):
        answer = await remote_controller.send_command(
            commands.DebugTest(DEFAULT_PROCEDURE_SETUP_DEBUG_INDEX),
            raise_exception=False,
        )
        if answer.is_valid and not answer.is_error_msg:
            return

    atf_values = [500000, 1000000, 3000000, 4000000]
    for index, atf_value in enumerate(atf_values, start=1):
        await remote_controller.send_command(commands.SetAtf(index, atf_value))
        await remote_controller.send_command(commands.SetAtk(index, 0))
        await remote_controller.send_command(commands.SetAtt(index, 0))

    await remote_controller.send_command(commands.SetRampFStart(1_000_000))
    await remote_controller.send_command(commands.SetRampFStop(2_000_000))
    await remote_controller.send_command(commands.SetRampFStep(100_000))
    await remote_controller.send_command(commands.SetRampTOn(500))
    await remote_controller.send_command(commands.SetRampTOff(0))
    await remote_controller.send_command(commands.SetRampGain(50))

    await remote_controller.send_command(commands.SetWipeFRange(8_000))
    await remote_controller.send_command(commands.SetWipeFStep(10))
    await remote_controller.send_command(commands.SetWipeTOn(500))
    await remote_controller.send_command(commands.SetWipeTOff(20))
    await remote_controller.send_command(commands.SetWipeTPause(2_000))
    await remote_controller.send_command(commands.SetWipeGain(150))


async def reset_at1_config_over_serial_monitor(
    send_command: Callable[[str, bool], Awaitable[str]],
) -> None:
    answer = await send_command(f"!debug_test{RESET_AT1_CONFIG_DEBUG_INDEX}", True)
    if _raw_answer_is_success(answer):
        return

    await send_command("!atf1=0", False)
    await send_command("!att1=0", False)
    await send_command("!atk1=0", False)


async def reset_at1_config_over_device(device: SonicDevice) -> None:
    if _supports_debug_test(device):
        answer = await device.execute_command(
            commands.DebugTest(RESET_AT1_CONFIG_DEBUG_INDEX),
            raise_exception=False,
        )
        if answer.is_valid and not answer.is_error_msg:
            return

    await device.execute_command(commands.SetAtf(1, 0))
    await device.execute_command(commands.SetAtt(1, 0))
    await device.execute_command(commands.SetAtk(1, 0))