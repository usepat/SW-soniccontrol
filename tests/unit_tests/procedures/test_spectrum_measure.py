import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from soniccontrol.procedures.holder import Holder, HolderArgs
from soniccontrol.procedures.procs.spectrum_measure import SpectrumMeasure


@pytest.mark.asyncio
async def test_ramp_waits_for_update_before_next_frequency(monkeypatch):
    updater = Mock()
    update_started = asyncio.Event()
    release_update = asyncio.Event()

    async def update_side_effect():
        update_started.set()
        await release_update.wait()

    updater.update = AsyncMock(side_effect=update_side_effect)
    spectrum_measure = SpectrumMeasure(updater)

    device = Mock()
    device.execute_command = AsyncMock()
    device.set_signal_on = AsyncMock()
    device.set_signal_off = AsyncMock()

    holder_execute = AsyncMock()
    monkeypatch.setattr(Holder, "execute", holder_execute)

    ramp_task = asyncio.create_task(
        spectrum_measure._ramp(
            device,
            values=[100, 200],
            hold_on=HolderArgs(10, "ms"),
            hold_off=Mock(duration=0),
            time_offset_measure=HolderArgs(5, "ms"),
        )
    )

    await update_started.wait()
    await asyncio.sleep(0)

    assert device.execute_command.await_count == 1
    assert updater.update.await_count == 1

    release_update.set()
    await ramp_task

    assert device.execute_command.await_count == 2
    assert updater.update.await_count == 2
    device.set_signal_on.assert_awaited_once()
    device.set_signal_off.assert_not_awaited()
    assert holder_execute.await_count == 4


@pytest.mark.asyncio
async def test_request_stop_interrupts_waits_without_extra_commands():
    updater = Mock()
    updater.update = AsyncMock()
    spectrum_measure = SpectrumMeasure(updater)

    device = Mock()
    device.execute_command = AsyncMock()
    device.set_signal_on = AsyncMock()
    device.set_signal_off = AsyncMock()

    ramp_task = asyncio.create_task(
        spectrum_measure._ramp(
            device,
            values=[100, 200],
            hold_on=HolderArgs(1, "s"),
            hold_off=Mock(duration=0),
            time_offset_measure=HolderArgs(500, "ms"),
        )
    )

    await asyncio.sleep(0)
    spectrum_measure.request_stop()

    with pytest.raises(asyncio.CancelledError):
        await ramp_task

    assert device.execute_command.await_count == 1