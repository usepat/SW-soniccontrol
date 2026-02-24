from typing import Any, Generator
import pytest
from unittest.mock import Mock
import asyncio

from soniccontrol.scripting.interpreter_engine import InterpreterEngine, InterpreterState
from soniccontrol.sonic_device import SonicDevice
from soniccontrol.updater import Updater
from soniccontrol.scripting.new_scripting import NewScriptingFacade, RunnableScript, ExecutionStep


@pytest.fixture
def interpreter_engine():
    device = Mock(SonicDevice)
    updater = Mock(Updater)
    interpreter = InterpreterEngine(device, updater)
    interpreter._set_interpreter_state = Mock(wraps=interpreter._set_interpreter_state)
    
    return interpreter

class ScriptSpy(RunnableScript):
    def __init__(self, script: RunnableScript | str):
        if isinstance(script, str):
            script = NewScriptingFacade().parse_script(script)
        self._script = script
        self._iter = iter(self._script)
        self._mocked_next = Mock(wraps=self._next)
    
    def _next(self) -> ExecutionStep:
        return next(self._iter)

    def __iter__(self) -> Generator[ExecutionStep, Any, None]: 
        self._iter = iter(self._script)
        return self
    
    def __next__(self) -> ExecutionStep:
        return self._mocked_next()

    @property
    def mocked_next(self):
        return self._mocked_next


@pytest.mark.asyncio()
async def test_start_runs_script(interpreter_engine):
    script = ScriptSpy("""
    on
    hold 100ms
    off
    frequency 100000
""")
    interpreter_engine.script = script
    
    assert interpreter_engine.interpreter_state == InterpreterState.READY
    interpreter_engine.start()
    assert interpreter_engine.interpreter_state == InterpreterState.RUNNING
    await interpreter_engine.wait_for_script_to_halt()
    assert interpreter_engine.interpreter_state == InterpreterState.READY
    assert script.mocked_next.call_count == 5 # number of statements + 1, because StopIteration has to be raised

@pytest.mark.asyncio()
async def test_script_can_be_started_again_after_finishing(interpreter_engine):
    script = ScriptSpy("""
    on
    off
""")
    interpreter_engine.script = script
    assert interpreter_engine.interpreter_state == InterpreterState.READY   

    interpreter_engine.start()
    await interpreter_engine.wait_for_script_to_halt()
    assert interpreter_engine.interpreter_state == InterpreterState.READY
    assert script.mocked_next.call_count == 3
    script.mocked_next.call_count = 0 # reset call count to zero

    interpreter_engine.start()
    await asyncio.wait_for(interpreter_engine.wait_for_script_to_halt(), 1)
    assert interpreter_engine.interpreter_state == InterpreterState.READY
    assert script.mocked_next.call_count == 3


@pytest.mark.asyncio()
async def test_stop_running_script(interpreter_engine):
    script = ScriptSpy("""
    hold 1s
    off
""")
    interpreter_engine.script = script 
    interpreter_engine.start()
    assert interpreter_engine.interpreter_state == InterpreterState.RUNNING
    await asyncio.sleep(0.1)

    await interpreter_engine.stop()  
    assert interpreter_engine.interpreter_state == InterpreterState.READY

@pytest.mark.asyncio()
async def test_pause_running_script(interpreter_engine):
    script = ScriptSpy("""
    hold 1s
    off
""")
    interpreter_engine.script = script 
    interpreter_engine.start()
    assert interpreter_engine.interpreter_state == InterpreterState.RUNNING
    await asyncio.sleep(0.1)

    await interpreter_engine.pause()  
    assert interpreter_engine.interpreter_state == InterpreterState.PAUSED


@pytest.mark.asyncio()
async def test_single_step_only_executes_one_instruction(interpreter_engine):
    script = ScriptSpy("""
    on
    off
""")
    interpreter_engine.script = script

    interpreter_engine.single_step()
    await asyncio.wait_for(interpreter_engine.wait_for_script_to_halt(), 1)
    assert interpreter_engine.interpreter_state == InterpreterState.PAUSED

@pytest.mark.asyncio()
async def test_single_step_stop_resets_interpreter_engine(interpreter_engine):
    script = ScriptSpy("""
    on
    off
""")
    interpreter_engine.script = script

    interpreter_engine.single_step()
    await asyncio.wait_for(interpreter_engine.wait_for_script_to_halt(), 1)
    assert interpreter_engine.interpreter_state == InterpreterState.PAUSED

    await interpreter_engine.stop()
    assert interpreter_engine.interpreter_state == InterpreterState.READY
    script.mocked_next.assert_called_once()

@pytest.mark.asyncio()
async def test_calling_single_step_until_script_finished(interpreter_engine):
    script = ScriptSpy("""
    on
    off
    on
    off
    on
""")
    interpreter_engine.script = script

    for _ in range(5):
        interpreter_engine.single_step()
        await asyncio.wait_for(interpreter_engine.wait_for_script_to_halt(), 1)
        assert interpreter_engine.interpreter_state == InterpreterState.PAUSED

    interpreter_engine.single_step()
    await asyncio.wait_for(interpreter_engine.wait_for_script_to_halt(), 1)
    assert interpreter_engine.interpreter_state == InterpreterState.READY

@pytest.mark.asyncio()
async def test_breakpoint_pauses_script(interpreter_engine):
    script = ScriptSpy("""
    off
    breakpoint
    on
""")
    interpreter_engine.script = script 
    interpreter_engine.start()
    await asyncio.wait_for(interpreter_engine.wait_for_script_to_halt(), 1)
    assert interpreter_engine.interpreter_state == InterpreterState.PAUSED
    assert script.mocked_next.call_count == 2

@pytest.mark.asyncio()
async def test_paused_script_can_be_resumed(interpreter_engine):
    script = ScriptSpy("""
    off
    breakpoint
    on
    on
""")
    interpreter_engine.script = script 

    interpreter_engine.start()
    # break point pauses execution
    await interpreter_engine.wait_for_script_to_halt()
    assert script.mocked_next.call_count == 2

    interpreter_engine.start()
    # continue until finished
    await interpreter_engine.wait_for_script_to_halt()
    assert script.mocked_next.call_count == 5

@pytest.mark.asyncio()
async def test_paused_script_can_be_restarted(interpreter_engine):
    script = ScriptSpy("""
    off
    breakpoint
    on
    on
""")
    interpreter_engine.script = script 

    interpreter_engine.start()
    # break point pauses execution
    await interpreter_engine.wait_for_script_to_halt()
    assert interpreter_engine.interpreter_state == InterpreterState.PAUSED

    await interpreter_engine.stop()
    assert interpreter_engine.interpreter_state == InterpreterState.READY
    
    # restart script
    interpreter_engine.start()
    # break point pauses execution
    await interpreter_engine.wait_for_script_to_halt()
    # continue until finished
    interpreter_engine.start()
    await interpreter_engine.wait_for_script_to_halt()
    assert interpreter_engine.interpreter_state == InterpreterState.READY


@pytest.mark.asyncio()
async def test_paused_script_can_be_continued_by_single_step(interpreter_engine):
    script = ScriptSpy("""
    off
    breakpoint
    on
    on
""")
    interpreter_engine.script = script 

    interpreter_engine.start()
    # break point pauses execution
    await interpreter_engine.wait_for_script_to_halt()
    assert script.mocked_next.call_count == 2

    interpreter_engine.single_step()
    await interpreter_engine.wait_for_script_to_halt()
    assert script.mocked_next.call_count == 3

@pytest.mark.asyncio()
async def test_exception_stops_script(interpreter_engine):
    script = ScriptSpy("""
    off
    on
    frequency "error"
    off
    on
""")
    interpreter_engine.script = script 

    interpreter_engine.start()
    await interpreter_engine.wait_for_script_to_halt()
    assert interpreter_engine.interpreter_state == InterpreterState.READY
    assert script.mocked_next.call_count == 3


