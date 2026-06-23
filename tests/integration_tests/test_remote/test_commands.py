import attrs
import cattrs
from soniccontrol import DeviceParamConstantType, Answer, EFieldName, DeviceType, CommandCode
from sonic_protocol.python_parser import commands
from tests.integration_tests.test_remote.conftest import format_command, reset_remote_controller_state, resolve_protocol_arg

from sonic_pytest.remote_controller.asserts import assert_answer, assert_answer_is_not_error
import pytest
from sonic_protocol.user_manual_compiler.deduce_command_examples import deduce_command_examples_as_commands
import allure
import json
from allure_commons.lifecycle import AllureLifecycle 
from allure_commons.model2 import Status, StatusDetails

@pytest.mark.asyncio(loop_scope="package")
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
    assert answer.valid, "Answer should be valid"

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
                    CommandCode.E_PARSING_ERROR, 
                    CommandCode.E_SYNTAX_ERROR
                ])
            except AssertionError as e:
                if answer.message == "Modbus does not support commands with string index parameters":
                    continue
                errors.append(DeducedCommandError(command, answer, i, str(e)))
                lifecycle = AllureLifecycle()
                lifecycle.update_step(
                    lambda step_result, err=e: step_result.update(
                        status=Status.FAILED,
                        statusDetails=StatusDetails(message=str(err))
                    )
                )
                progress_writer(f"Error: {answer}, {e}")

        await reset_remote_controller_state(remote_controller)

    error_json = json.dumps([{ 
        "full_error_msg": str(e), 
        "index": e.step, 
        "command": {
            "code": e.command.code.name, 
            "args": cattrs.Converter().unstructure(e.command.args)
        }, 
        "answer": e.answer.message, 
        "assert_msg": e.assert_msg 
    } for e in errors ])
    allure.attach(
        error_json,
        attachment_type=allure.attachment_type.JSON
    )
    assert len(errors) == 0, "Errors occurred"


@pytest.mark.asyncio(loop_scope="package")
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
    assert not answer.valid, "Answer should be not valid"


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
    assert answer.valid, "Answer was not valid"


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
    assert answer.valid, "Answer should be valid, because the param is in the bounds"

    invalid_command = command_builder(const_value + (+1 if is_upper_bound else -1))
    answer = await remote_controller.send_command(invalid_command)
    assert not answer.valid, "Answer should be not valid, because param is expected to be out of bounds"


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
