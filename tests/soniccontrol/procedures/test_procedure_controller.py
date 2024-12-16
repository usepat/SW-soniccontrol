import asyncio
import pytest
from unittest.mock import Mock, AsyncMock
import logging
from soniccontrol.events import Event, EventManager
from soniccontrol.procedures.holder import HolderArgs
from soniccontrol.procedures.procedure_instantiator import ProcedureInstantiator
from soniccontrol.procedures.procedure_controller import ProcedureController, ProcedureType
from soniccontrol.sonic_device import SonicDevice
from soniccontrol.procedures.procs.ramper import RamperArgs, RamperLocal


@pytest.fixture
def proc_controller(monkeypatch, request):
    ramp = request.param
    # We have to patch the function in the module it is used and not in the module where it is declared
    monkeypatch.setattr("soniccontrol.procedures.procedure_controller.get_base_logger", lambda _: logging.getLogger())
    monkeypatch.setattr(ProcedureInstantiator, "instantiate_ramp", Mock(return_value=ramp))
    proc_controller = ProcedureController(Mock(spec=SonicDevice), Mock(spec=EventManager))

    return proc_controller

@pytest.mark.asyncio
@pytest.mark.parametrize("proc_controller", [RamperLocal()], indirect=True)
async def test_stop_raises_event_exactly_once(monkeypatch, proc_controller):
    proc_execute = AsyncMock()
    monkeypatch.setattr(RamperLocal, "execute", proc_execute)
    listener = Mock()
    proc_controller.subscribe(ProcedureController.PROCEDURE_STOPPED, listener)

    proc_controller.execute_proc(ProcedureType.RAMP, Mock(spec=RamperArgs))
    await asyncio.sleep(0.1)

    listener.assert_called_once_with(Event(ProcedureController.PROCEDURE_STOPPED))

@pytest.mark.asyncio
@pytest.mark.parametrize("proc_controller", [RamperLocal()], indirect=True)
async def test_execute_proc_throws_error_if_a_proc_already_is_running(proc_controller):
    listener = Mock()
    proc_controller.subscribe(ProcedureController.PROCEDURE_STOPPED, listener)

    proc_controller.execute_proc(ProcedureType.RAMP, RamperArgs(1000, 500, 10, HolderArgs(1, "ms"), HolderArgs(1, "ms")))
    
    with pytest.raises(Exception):
        proc_controller.execute_proc(ProcedureType.RAMP, Mock(spec=RamperArgs))


@pytest.mark.parametrize("proc_controller", [None], indirect=True)
def test_execute_proc_throws_error_if_proc_not_available(proc_controller):
    with pytest.raises(Exception):
        proc_controller.execute_proc(ProcedureType.RAMP, None)
    

@pytest.mark.asyncio
@pytest.mark.parametrize("proc_controller", [RamperLocal()], indirect=True)
async def test_execute_proc_executes_procedure(monkeypatch, proc_controller):
    proc_execute = AsyncMock()
    monkeypatch.setattr(RamperLocal, "execute", proc_execute)
    listener = Mock()
    proc_controller.subscribe(ProcedureController.PROCEDURE_STOPPED, listener)

    proc_controller.execute_proc(ProcedureType.RAMP, Mock(spec=RamperArgs))
    
    assert proc_controller.is_proc_running
    await asyncio.sleep(0.1)
    proc_execute.assert_called_once()