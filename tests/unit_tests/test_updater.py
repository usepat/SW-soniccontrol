import asyncio
import logging
from types import SimpleNamespace

import pytest

from soniccontrol.communication.modbus_communicator import ModbusCommunicator
from soniccontrol.updater import Updater


@pytest.mark.asyncio
async def test_stop_does_not_cancel_modbus_daemon():
    cancelled = False

    async def daemon_coro() -> None:
        nonlocal cancelled
        try:
            await asyncio.sleep(0)
        except asyncio.CancelledError:
            cancelled = True
            raise

    device = SimpleNamespace(
        _logger=logging.getLogger("test"),
        communicator=ModbusCommunicator(),
    )
    updater = Updater(device)
    updater.running.set()
    updater._daemon = asyncio.create_task(daemon_coro())

    await updater.stop()

    assert not cancelled
    assert updater._daemon is None
    assert not updater.running.is_set()


@pytest.mark.asyncio
async def test_stop_cancels_non_modbus_daemon():
    cancelled = False

    async def daemon_coro() -> None:
        nonlocal cancelled
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            cancelled = True
            raise

    device = SimpleNamespace(
        _logger=logging.getLogger("test"),
        communicator=SimpleNamespace(),
    )
    updater = Updater(device)
    updater.running.set()
    updater._daemon = asyncio.create_task(daemon_coro())
    await asyncio.sleep(0)

    await updater.stop()

    assert cancelled
    assert updater._daemon is None
    assert not updater.running.is_set()
