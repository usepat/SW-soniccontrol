import pytest
from unittest.mock import Mock

from soniccontrol.procedures.holder import HolderArgs
from soniccontrol.scripting.new_scripting import NewScriptingFacade, Interpreter
from soniccontrol.scripting.scripting_facade import ScriptException


@pytest.fixture
def command_mocks(monkeypatch):
    mocks = {}
    for name, func in Interpreter.FUNCTION_TABLE.items():
        async def mocked_command(_, __):
            pass
        
        mock = Mock()
        mock.parameters = func.parameters
        mock.create_command.return_value = (name, mocked_command)
        
        monkeypatch.setitem(Interpreter.FUNCTION_TABLE, name, mock)
        mocks[name] = mock
    return mocks

def test_interpreter_calls_function(command_mocks):
    test_script = """
        on
        off
    """
    runnable_script = NewScriptingFacade().parse_script(test_script)
    for _ in runnable_script:
        pass
    command_mocks["on"].create_command.assert_called_once()
    command_mocks["off"].create_command.assert_called_once()

@pytest.mark.parametrize(["script", "command_name", "params"], [
    ("send \"!freq=1000\"\n", "send", ("!freq=1000",)),
    ("hold 100ms\n", "hold", (HolderArgs(100, "ms"),)),
    ("frequency 100000\n", "frequency", (100000,)),
    ("ramp 100000 200000 10000 5s 500ms\n", "ramp", (100000, 200000, 10000, HolderArgs(5, "s"), HolderArgs(500, "ms"))),
])
def test_interpreter_calls_function_with_params(script, command_name, params, command_mocks):
    runnable_script = NewScriptingFacade().parse_script(script)
    list(runnable_script) # Fully run the script to trigger all commands
    command_mocks[command_name].create_command.assert_called_once_with(*params)

def test_interpreter_loops_n_times(command_mocks):
    n_times = 5
    script = f"""
        off
        loop {n_times} times
        begin
            on
        end
    """
    runnable_script = NewScriptingFacade().parse_script(script)
    list(runnable_script) # Fully run the script to trigger all commands
    command_mocks["on"].create_command.call_count = n_times
    command_mocks["off"].create_command.call_count = 1

def test_interpreter_ignores_empty_lines_and_comments(command_mocks):
    script = """
        /*
            This is a comment
            off
        */

        // This is also a comment

        off
        
        # And this? This is also a comment ;)
        
        on

        loop 6 times
        begin 
            send "off"
            // look at alle those empty lines in this block

        end
    """
    runnable_script = NewScriptingFacade().parse_script(script)
    list(runnable_script) 
    command_mocks["on"].create_command.assert_called_once()
    command_mocks["off"].create_command.assert_called_once()
    
@pytest.mark.parametrize("script", [
     """
        loop 5 times
        begin 

    """,
    """
        loop 5
        begin 
            on
        end
    """, 
    "5",   
    "\"string\"",   
    """
    section
    begin
       on 
    end
    """,
    """
    loop 5 times
       on 
    """,
     """
    loop 5 times
    section lasts 5s
    begin
        on
    end
    """
])
def test_interpreter_throws_if_wrong_syntax(script):
    with pytest.raises(ScriptException):
        runnable_script = NewScriptingFacade().parse_script(script)
        list(runnable_script) 

def test_interpreter_throws_if_unknown_function(command_mocks):
    script = "some_func 1000 100ms"
    with pytest.raises(ScriptException):
        runnable_script = NewScriptingFacade().parse_script(script)
        list(runnable_script) 

@pytest.mark.parametrize("script", [
    "hold",
    "hold 1000ms 100s",  
    "off true"
])
def test_interpreter_throws_if_wrong_num_params(script, command_mocks):
    with pytest.raises(ScriptException):
        runnable_script = NewScriptingFacade().parse_script(script)
        list(runnable_script) 

@pytest.mark.parametrize("script", [
    "hold \"200ms\"",
    "frequency 100ms",  
    "send 100",
    "send true",
    "gain \"a lot\""  
])
def test_interpreter_throws_if_wrong_param_type(script, command_mocks):
    with pytest.raises(ScriptException):
        runnable_script = NewScriptingFacade().parse_script(script)
        list(runnable_script) 



