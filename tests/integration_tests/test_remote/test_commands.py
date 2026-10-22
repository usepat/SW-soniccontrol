import json
import logging

import attrs
import allure
import cattrs
import pytest
from sonic_protocol.python_parser import commands
from sonic_protocol.user_manual_compiler.deduce_command_examples import deduce_command_examples_as_commands
from soniccontrol import Answer, CommandCode, DeviceParamConstantType, DeviceType, EFieldName
from soniccontrol.data_capturing.converter import register_unstructure_hooks_for_numpy
from sonic_pytest.remote_controller.asserts import assert_answer, assert_answer_is_not_error
from tests.integration_tests.test_remote.conftest import reset_remote_controller_state, resolve_protocol_arg


@pytest.mark.asyncio(loop_scope="package")
@pytest.mark.skip_if_modbus_enabled
@pytest.mark.parametrize("formatted_command_str", [
    ("!g={}", DeviceParamConstantType.MIN_GAIN),
    ("!gain={}", DeviceParamConstantType.MIN_GAIN),
    ("set_gain={}", DeviceParamConstantType.MIN_GAIN),
    ("-", None),
    ("get_update", None),
    ("?g", None),
    ("?gain", None),
    ("get_gain", None),
], indirect=True)
async def test_if_aliases_are_working(formatted_command_str, remote_controller):
    if remote_controller._device._uses_modbus():
        pytest.skip("Command aliases only apply to sonic text communication, not Modbus")

    answer = await remote_controller.send_command(formatted_command_str)
    assert answer.is_valid, "Answer should be valid"

@pytest.mark.asyncio(loop_scope="package")
async def test_if_gain_can_be_set_and_retrieved(remote_controller):
    consts = remote_controller.protocol_consts

    await remote_controller.send_command(commands.SetGain(consts.min_gain))
    answer = await remote_controller.send_command(commands.GetGain())
    assert_answer(answer, { EFieldName.GAIN: consts.min_gain })

    await remote_controller.send_command(commands.SetGain(consts.max_gain))
    answer = await remote_controller.send_command(commands.GetGain())
    assert_answer(answer, { EFieldName.GAIN: consts.max_gain })
    

@pytest.mark.skip_remote_test_setup
@pytest.mark.asyncio(loop_scope="package")
async def test_deduced_commands(remote_controller, progress_writer):
    remote_controller.device._logger.setLevel(logging.ERROR)
    if hasattr(remote_controller.device.communicator, "_logger"):
        # This is required because the PostmanProxy has no logger
        remote_controller.device.communicator._logger.setLevel(logging.ERROR)

    @attrs.define()
    class DeducedCommandError(Exception):
        command: commands.Command = attrs.field()
        answer: Answer = attrs.field()
        step: int = attrs.field()
        assert_msg: str = attrs.field()

        def __str__(self) -> str:
            return f"Error on {self.step}-th command:\n" + \
                    f"'{self.command.code.name} {self.command.args}' returned '{self.answer.message}'\n" + \
                    f"triggered assertion: '{self.assert_msg}'"

    converter = cattrs.Converter()
    register_unstructure_hooks_for_numpy(converter)

    def format_deduced_command_error(error: DeducedCommandError, total_commands: int) -> str:
        command_args = json.dumps(converter.unstructure(error.command.args), sort_keys=True)
        answer_code = error.answer.command_code.name if error.answer.command_code is not None else "None"
        return (
            f"Deduced command failure at step {error.step + 1}/{total_commands}: "
            f"{error.command.code.name} args={command_args}; "
            f"answer_code={answer_code}; answer_valid={error.answer.valid.name}; "
            f"answer_message={error.answer.message!r}; assertion={error.assert_msg}"
        )


    info = remote_controller.device_info
    commands_to_skip = [
        CommandCode.SONIC_FORCE,
        CommandCode.GO_INTO_DEVICE_STATE,
        CommandCode.START_CONFIGURATOR,
        CommandCode.START_OPERATOR,
        CommandCode.START_DIAGNOSTIC_TOOL,
        CommandCode.RESTART_DEVICE,
        CommandCode.SET_FLASH_115200,
        CommandCode.SET_FLASH_9600,
        CommandCode.SET_FLASH_USB,
        CommandCode.START_CUSTOMIZER
    ]

    if info.device_type != DeviceType.DIAGNOSTICS_TOOL:
        # only the diagnostics tool can execute those commands
        # FIXME: this quick fix is needed here, because the architecture of the protocol is not as good as it should be.
        # There should be a full set of fixed commands and the applications should only state, which sub set of them they can execute.
        # The inheritance approach that we currently have is not that good.
        # Related to usepat/SW-soniccontrol#234
        commands_to_skip.extend([
            CommandCode.GET_NUM_TESTS,
            CommandCode.GET_TEST_INFO, 
            CommandCode.GET_TEST_VALIDATION_ARG,
            CommandCode.RUN_TEST,
            CommandCode.ABORT_TEST,
        ])

    deduced_commands = deduce_command_examples_as_commands(
        info.protocol_version, info.device_type, info.is_release, 
        skip_command_codes=commands_to_skip
    )

    num_commands = len(deduced_commands)
    errors = []
    for i, command in enumerate(deduced_commands):
        progress_writer(f"executing {i + 1}/{num_commands}: {command.code.name} {command.args}")
        with allure.step(f"executing {i}/{num_commands}: '{command.code.name} {command.args}'"):
            answer = await remote_controller.send_command(command)
            try:
                assert_answer_is_not_error(answer, errors_to_check=[
                    CommandCode.E_INTERNAL_DEVICE_ERROR, 
                    CommandCode.E_COMMAND_NOT_KNOWN, 
                    CommandCode.E_COMMAND_NOT_IMPLEMENTED,
                    CommandCode.E_PARSING_ERROR, 
                    CommandCode.E_SYNTAX_ERROR,
                ])
                assert remote_controller.is_connected, "The remote controller got disconnected"
            except AssertionError as e:
                if answer.message == "Modbus does not support commands with string index parameters":
                    continue
                error = DeducedCommandError(command, answer, i, str(e))
                errors.append(error)
                error_summary = format_deduced_command_error(error, num_commands)
                progress_writer(error_summary)
                remote_controller.device._logger.error(error_summary)

        await reset_remote_controller_state(remote_controller)

    error_json = json.dumps([{ 
        "full_error_msg": str(e), 
        "index": e.step, 
        "command": {
            "code": e.command.code.name, 
            "args": converter.unstructure(e.command.args)
        }, 
        "answer": e.answer.message, 
        "assert_msg": e.assert_msg 
    } for e in errors ])
    allure.attach(
        error_json,
        attachment_type=allure.attachment_type.JSON
    )

    if errors:
        error_summary = "\n".join(format_deduced_command_error(error, num_commands) for error in errors)
        allure.attach(
            error_summary,
            name="deduced_command_failures",
            attachment_type=allure.attachment_type.TEXT,
        )
        pytest.fail(f"Errors occurred during deduced commands:\n{error_summary}")


@pytest.mark.asyncio(loop_scope="package")
@pytest.mark.skip_if_modbus_enabled
@pytest.mark.parametrize("formatted_command_str", [
    ("!gain=-1000", []),
    ("!gain=", []),
    ("!gain{}", [DeviceParamConstantType.MIN_TRANSDUCER_INDEX]),
    ("!gain", []),
    ("!gain=asdf", []),
    ("?gain={}", [DeviceParamConstantType.MIN_GAIN]),
    ("?gain{}", [DeviceParamConstantType.MIN_TRANSDUCER_INDEX]),
    ("?gainappendedtext", []),
], indirect=True)
async def test_if_invalid_syntax_throws_error(remote_controller, formatted_command_str):
    if remote_controller._device._uses_modbus():
        pytest.skip("Invalid string syntax tests only apply to sonic text communication, not Modbus")

    answer = await remote_controller.send_command(formatted_command_str)
    assert not answer.is_valid, "Answer should be not valid"


@pytest.mark.allowed_devices(DeviceType.MVP_WORKER, DeviceType.POSTMAN)
@pytest.mark.asyncio(loop_scope="package")
@pytest.mark.parametrize("command_builder", [
    pytest.param(lambda consts: commands.SetGain(100), id="set-gain"),
    pytest.param(lambda consts: commands.SetFrequency(consts.min_frequency), id="set-frequency"),
    pytest.param(lambda consts: commands.SetAtt(4, 0), id="set-att"),
    pytest.param(lambda consts: commands.SetAtk(1, 100), id="set-atk"),
    pytest.param(lambda consts: commands.SetAtf(2, consts.min_frequency), id="set-atf"),
    pytest.param(lambda consts: commands.SetWipeFStep(consts.min_frequency), id="set-wipe-f-step"),
    pytest.param(lambda consts: commands.SetWipeTOn(100), id="set-wipe-t-on"),
    pytest.param(lambda consts: commands.SetScanFStep(1000), id="set-scan-f-step"),
    pytest.param(lambda consts: commands.SetRampFStart(consts.min_frequency), id="set-ramp-f-start"),
    pytest.param(lambda consts: commands.SetTuneFStep(1000), id="set-tune-f-step"),
])
async def test_if_basic_setter_commands_work(remote_controller, command_builder):
    answer = await remote_controller.send_command(command_builder(remote_controller.protocol_consts))
    assert answer.is_valid, "Answer was not valid"


@pytest.mark.allowed_devices(DeviceType.MVP_WORKER, DeviceType.POSTMAN)
@pytest.mark.asyncio(loop_scope="package")
async def test_if_freq_set_by_setter_can_be_retrieved_with_getter(remote_controller):
    consts = remote_controller.protocol_consts

    await remote_controller.send_command(commands.SetFrequency(consts.min_frequency))
    answer = await remote_controller.send_command(commands.GetFreq())
    assert_answer(answer, {EFieldName.FREQUENCY: consts.min_frequency})

    await remote_controller.send_command(commands.SetFrequency(consts.max_frequency))
    answer = await remote_controller.send_command(commands.GetFreq())
    assert_answer(answer, {EFieldName.FREQUENCY: consts.max_frequency})

    await remote_controller.send_command(commands.SetAtf(consts.min_transducer_index, consts.min_frequency))
    answer = await remote_controller.send_command(commands.GetAtf(consts.min_transducer_index))
    assert_answer(answer, {EFieldName.ATF: consts.min_frequency})

    await remote_controller.send_command(commands.SetAtf(consts.min_transducer_index, consts.max_frequency))
    answer = await remote_controller.send_command(commands.GetAtf(consts.min_transducer_index))
    assert_answer(answer, {EFieldName.ATF: consts.max_frequency})

@pytest.mark.asyncio(loop_scope="package")
@pytest.mark.parametrize("command_builder, const, is_upper_bound", [
    (lambda value: commands.SetGain(value), DeviceParamConstantType.MAX_GAIN, True),
    (lambda value: commands.SetGain(value), DeviceParamConstantType.MIN_GAIN, False),
    pytest.param(lambda value: commands.GetAtf(value), DeviceParamConstantType.MAX_TRANSDUCER_INDEX, True, marks=pytest.mark.allowed_devices(DeviceType.MVP_WORKER)),
    pytest.param(lambda value: commands.GetAtf(value), DeviceParamConstantType.MIN_TRANSDUCER_INDEX, False, marks=pytest.mark.allowed_devices(DeviceType.MVP_WORKER)),
])
async def test_limits_of_parameter(remote_controller, command_builder, const, is_upper_bound):
    const_value = resolve_protocol_arg(const, remote_controller.protocol_consts)
    valid_command = command_builder(const_value)
    answer = await remote_controller.send_command(valid_command)
    assert answer.is_valid, "Answer should be valid, because the param is in the bounds"

    invalid_command = command_builder(const_value + (+1 if is_upper_bound else -1))
    answer = await remote_controller.send_command(invalid_command)
    assert not answer.is_valid, "Answer should be not valid, because param is expected to be out of bounds"


@pytest.mark.allowed_devices(DeviceType.DESCALE)
@pytest.mark.asyncio(loop_scope="package")
async def test_if_swf_set_by_setter_can_be_retrieved_with_getter(remote_controller):
    consts = remote_controller.protocol_consts

    await remote_controller.send_command(commands.SetSwf(consts.min_swf))
    answer = await remote_controller.send_command(commands.GetSwf())
    assert_answer(answer, {EFieldName.SWF: consts.min_swf})

    await remote_controller.send_command(commands.SetSwf(consts.max_swf))
    answer = await remote_controller.send_command(commands.GetSwf())
    assert_answer(answer, {EFieldName.SWF: consts.max_swf})
