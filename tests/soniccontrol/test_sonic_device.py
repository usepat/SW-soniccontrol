import pytest
from unittest.mock import Mock, AsyncMock

from sonic_protocol.defs import AnswerDef, AnswerFieldDef, CommandCode, CommandContract, CommandDef, CommandParamDef, DeviceType, FieldType, Protocol, ProtocolType, SonicTextCommandAttrs, Version
from sonic_protocol.field_names import EFieldName
import sonic_protocol.python_parser.commands as cmds
from soniccontrol.device_data import FirmwareInfo
from soniccontrol.sonic_device import SonicDevice
from soniccontrol.communication.communicator import Communicator


@pytest.fixture
def simple_protocol():
    return Protocol(info=ProtocolType(Version(1, 0, 0), DeviceType.UNKNOWN), command_contracts={
        CommandCode.GET_GAIN: CommandContract(
            CommandCode.GET_GAIN,
            CommandDef(SonicTextCommandAttrs(["?g", "?gain"])), 
            AnswerDef([AnswerFieldDef(EFieldName.GAIN, FieldType(int))])
        ),
        CommandCode.SET_FREQ: CommandContract(
            CommandCode.SET_FREQ,
            CommandDef(SonicTextCommandAttrs(["!f", "!freq", "!frequency"]), setter_param=CommandParamDef(EFieldName.FREQUENCY, FieldType(int))), 
            AnswerDef([AnswerFieldDef(EFieldName.FREQUENCY, FieldType(int))]),
        ),
        CommandCode.SET_GAIN: CommandContract(
            CommandCode.SET_GAIN,
            CommandDef(SonicTextCommandAttrs(["!g", "!gain"]), setter_param=CommandParamDef(EFieldName.GAIN, FieldType(int))), 
            AnswerDef([AnswerFieldDef(EFieldName.GAIN, FieldType(int))]),
        ),
        CommandCode.SET_ON: CommandContract(
            CommandCode.SET_ON,
            CommandDef(SonicTextCommandAttrs("!ON")), 
            AnswerDef([AnswerFieldDef(EFieldName.SIGNAL, FieldType(bool))]),
        ),
        CommandCode.SET_ATF: CommandContract(
            CommandCode.SET_ATF,
            CommandDef(
                SonicTextCommandAttrs("!atf"), 
                       index_param=CommandParamDef(EFieldName.INDEX, FieldType(int)), 
                       setter_param=CommandParamDef(EFieldName.ATF, FieldType(int))
            ), 
            AnswerDef([AnswerFieldDef(EFieldName.ATF, FieldType(int))]),
        ),
    })

@pytest.fixture
def communicator():
    communicator = Mock(Communicator) 
    communicator.send_and_wait_for_response = AsyncMock(return_value="")
    return communicator

@pytest.fixture
def sonic_device(communicator, simple_protocol):
    return SonicDevice(communicator, simple_protocol, FirmwareInfo())


@pytest.mark.asyncio
@pytest.mark.parametrize("command, request_str", [
    (cmds.SetFrequency(1000), "!f=1000"),
    (cmds.SetFrequency(420), "!f=420"),
    (cmds.SetGain(1000), "!g=1000"),
    (cmds.GetGain(), "?g"),
    (cmds.SetOn(), "!ON"),
    (cmds.SetAtf(4, 10000), "!atf4=10000"),
])
async def test_send_command_creates_correct_request(command, request_str, communicator, sonic_device):
    _ = await sonic_device._send_command(command)

    args, kwargs = communicator.send_and_wait_for_response.call_args  
    assert args == (request_str,)


