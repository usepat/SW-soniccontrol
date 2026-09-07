import asyncio
import pytest
from unittest.mock import Mock, AsyncMock
import logging

import pytest_asyncio
from sonic_protocol.python_parser.answer import Answer
from sonic_protocol.python_parser import commands
from soniccontrol.utils.events import Event
from soniccontrol.procedures.holder import HolderArgs
from soniccontrol.procedures.procedure_instantiator import ProcedureInstantiator
from soniccontrol.procedures.procedure_controller import ProcedureController, ProcedureType
from soniccontrol.sonic_device import SonicDevice
from soniccontrol.procedures.procs.ramper import RamperArgs, RamperLocal
from soniccontrol.updater import Updater



@pytest_asyncio.fixture
async def proc_controller(request):
    proc_name = request.param

    # We have to patch the function in the module it is used and not in the module where it is declared
    proc_controller = ProcedureController(Mock(spec=SonicDevice), Mock(spec=Updater), logging.getLogger())
    await proc_controller.load_procs()

    if proc_name == "ramper_local":
        proc_controller._procedures[ProcedureType.RAMP] = RamperLocal()

    return proc_controller

@pytest.mark.asyncio
@pytest.mark.parametrize("proc_controller", ["ramper_local"], indirect=True)
async def test_stop_raises_event_exactly_once(monkeypatch, proc_controller):
    proc_execute = AsyncMock()
    monkeypatch.setattr(RamperLocal, "execute", proc_execute)
    listener = Mock()
    proc_controller.subscribe(ProcedureController.PROCEDURE_STOPPED, listener)

    proc_controller.execute_proc(ProcedureType.RAMP, Mock(spec=RamperArgs))
    await asyncio.sleep(0.1)

    listener.assert_called_once_with(Event(ProcedureController.PROCEDURE_STOPPED))

@pytest.mark.asyncio
@pytest.mark.parametrize("proc_controller", ["ramper_local"], indirect=True)
async def test_execute_proc_throws_error_if_a_proc_already_is_running(proc_controller):
    procedure_args = RamperArgs.from_dict(
        f_start=1000, f_stop=500, f_step=10, t_on=HolderArgs(1, "s"), t_off=HolderArgs(1, "s") # type: ignore
    ) 
    proc_controller.execute_proc(ProcedureType.RAMP, procedure_args)
    
    with pytest.raises(Exception):
        proc_controller.execute_proc(ProcedureType.RAMP, Mock(spec=RamperArgs))


@pytest.mark.parametrize("proc_controller", ["none"], indirect=True)
def test_execute_proc_throws_error_if_proc_not_available(proc_controller):
    with pytest.raises(Exception):
        proc_controller.execute_proc(ProcedureType.RAMP, None)
    

@pytest.mark.asyncio
@pytest.mark.parametrize("proc_controller", ["ramper_local"], indirect=True)
async def test_execute_proc_executes_procedure(monkeypatch, proc_controller):
    proc_execute = AsyncMock()
    monkeypatch.setattr(RamperLocal, "execute", proc_execute)
    listener = Mock()
    proc_controller.subscribe(ProcedureController.PROCEDURE_STOPPED, listener)

    proc_controller.execute_proc(ProcedureType.RAMP, Mock(spec=RamperArgs))
    
    assert proc_controller.is_proc_running
    await asyncio.sleep(0.1)
    proc_execute.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("proc_controller", ["ramper_local"], indirect=True)
async def test_stop_proc_runs_cleanup_and_marks_proc_stopped(monkeypatch, proc_controller):
    proc_started = asyncio.Event()

    async def proc_execute(*_args, **_kwargs):
        proc_started.set()
        await asyncio.Future()

    monkeypatch.setattr(RamperLocal, "execute", proc_execute)
    proc_controller._device.set_signal_off = AsyncMock()
    listener = Mock()
    proc_controller.subscribe(ProcedureController.PROCEDURE_STOPPED, listener)

    proc_controller.execute_proc(ProcedureType.RAMP, Mock(spec=RamperArgs))
    await proc_started.wait()

    await proc_controller.stop_proc()

    proc_controller._device.set_signal_off.assert_awaited_once()
    listener.assert_called_once_with(Event(ProcedureController.PROCEDURE_STOPPED))
    assert not proc_controller.is_proc_running


@pytest.mark.asyncio
@pytest.mark.parametrize("proc_controller", ["ramper_local"], indirect=True)
async def test_stop_proc_prefers_cooperative_stop(monkeypatch, proc_controller):
    proc_started = asyncio.Event()
    allow_finish = asyncio.Event()

    async def proc_execute(*_args, **_kwargs):
        proc_started.set()
        await allow_finish.wait()

    request_stop = Mock(side_effect=lambda: allow_finish.set() or True)

    monkeypatch.setattr(RamperLocal, "execute", proc_execute)
    monkeypatch.setattr(RamperLocal, "request_stop", request_stop)

    proc_controller.execute_proc(ProcedureType.RAMP, Mock(spec=RamperArgs))
    await proc_started.wait()

    await proc_controller.stop_proc()

    request_stop.assert_called_once()
    assert not proc_controller.is_proc_running