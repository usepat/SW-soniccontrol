from unittest.mock import AsyncMock, Mock

import pytest

from soniccontrol.data_capturing.capture import Capture
from soniccontrol.data_capturing.capture_target import CaptureTarget


class DummyTarget(CaptureTarget):
    def __init__(self) -> None:
        super().__init__()
        self.after_end_capture_mock = AsyncMock()

    @property
    def args(self):
        return {}

    async def before_start_capture(self) -> None:
        return None

    def run_to_capturing_task(self) -> None:
        return None

    async def after_end_capture(self) -> None:
        await self.after_end_capture_mock()


@pytest.mark.asyncio
async def test_end_capture_emits_event_after_target_cleanup(tmp_path):
    capture = Capture(tmp_path)
    target = DummyTarget()
    capture._target = target
    capture._completed_capturing.clear()
    capture._experiment_writer = Mock()
    target.subscribe(CaptureTarget.COMPLETED_EVENT, capture.capture_target_completed_callback)

    call_order: list[str] = []

    async def after_end_capture() -> None:
        call_order.append("cleanup")

    target.after_end_capture_mock.side_effect = after_end_capture
    capture.subscribe(Capture.END_CAPTURE_EVENT, lambda _event: call_order.append("event"))

    await capture.end_capture()

    assert call_order == ["cleanup", "event"]


@pytest.mark.asyncio
async def test_end_capture_unsubscribes_completion_callback(tmp_path):
    capture = Capture(tmp_path)
    target = DummyTarget()
    capture._target = target
    capture._completed_capturing.clear()
    capture._experiment_writer = Mock()

    callback = capture.capture_target_completed_callback
    target.subscribe(CaptureTarget.COMPLETED_EVENT, callback)

    await capture.end_capture()

    listeners = target._listeners.get(CaptureTarget.COMPLETED_EVENT, set())
    assert callback not in listeners


@pytest.mark.asyncio
async def test_end_capture_is_idempotent(tmp_path):
    capture = Capture(tmp_path)
    target = DummyTarget()
    capture._target = target
    capture._completed_capturing.clear()
    capture._experiment_writer = Mock()

    await capture.end_capture()
    await capture.end_capture()

    target.after_end_capture_mock.assert_awaited_once()
