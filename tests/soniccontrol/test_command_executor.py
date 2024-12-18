import pytest
from unittest.mock import Mock, AsyncMock

from sonic_protocol.defs import AnswerDef, AnswerFieldDef, CommandCode, CommandDef, CommandParamDef, FieldType, SonicTextCommandAttrs
from sonic_protocol.field_names import EFieldName
from sonic_protocol.python_parser.answer import AnswerValidator
import sonic_protocol.python_parser.commands as cmds
from soniccontrol.command_executor import CommandExecutor
from soniccontrol.communication.communicator import Communicator
from sonic_protocol.protocol_builder import CommandLookUp, CommandLookUpTable


@pytest.fixture
def lookup_table() -> CommandLookUpTable:
    return {
        CommandCode.GET_GAIN: CommandLookUp(
            CommandDef(SonicTextCommandAttrs(["?g", "?gain"])), 
            AnswerDef([AnswerFieldDef(EFieldName.GAIN, FieldType(int))]),
            AnswerValidator("")
        ),
        CommandCode.SET_FREQ: CommandLookUp(
            CommandDef(SonicTextCommandAttrs(["!f", "!freq", "!frequency"]), setter_param=CommandParamDef(EFieldName.FREQUENCY, FieldType(int))), 
            AnswerDef([AnswerFieldDef(EFieldName.FREQUENCY, FieldType(int))]),
            AnswerValidator("")
        ),
        CommandCode.SET_GAIN: CommandLookUp(
            CommandDef(SonicTextCommandAttrs(["!g", "!gain"]), setter_param=CommandParamDef(EFieldName.GAIN, FieldType(int))), 
            AnswerDef([AnswerFieldDef(EFieldName.GAIN, FieldType(int))]),
            AnswerValidator(pattern="")
        ),
        CommandCode.SET_ON: CommandLookUp(
            CommandDef(SonicTextCommandAttrs("!ON")), 
            AnswerDef([AnswerFieldDef(EFieldName.SIGNAL, FieldType(bool))]),
            AnswerValidator("")
        ),
        CommandCode.SET_ATF: CommandLookUp(
            CommandDef(
                SonicTextCommandAttrs("!atf"), 
                       index_param=CommandParamDef(EFieldName.INDEX, FieldType(int)), 
                       setter_param=CommandParamDef(EFieldName.ATF, FieldType(int))
            ), 
            AnswerDef([AnswerFieldDef(EFieldName.ATF, FieldType(int))]),
            AnswerValidator("")
        ),
    }

@pytest.fixture
def communicator():
    communicator = Mock(Communicator) 
    communicator.send_and_wait_for_response = AsyncMock(return_value="")
    return communicator

@pytest.fixture
def command_executor(communicator, lookup_table):
    return CommandExecutor(lookup_table, communicator)


@pytest.mark.asyncio
@pytest.mark.parametrize("command, request_str", [
    (cmds.SetFrequency(1000), "!f=1000"),
    (cmds.SetFrequency(420), "!f=420"),
    (cmds.SetGain(1000), "!g=1000"),
    (cmds.GetGain(), "?g"),
    (cmds.SetOn(), "!ON"),
    (cmds.SetAtf(4, 10000), "!atf4=10000"),
])
async def test_send_command_creates_correct_request(command, request_str, communicator, command_executor):
    _ = await command_executor.send_command(command)

    communicator.send_and_wait_for_response.assert_called_once_with(request_str)    


