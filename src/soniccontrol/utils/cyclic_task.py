import asyncio
import logging
from contextlib import suppress
from typing import Any, Callable, Coroutine, Optional
import abc


class CyclicTask(abc.ABC):
    """
        This class calls a coroutine repeatedly, while waiting between iterations.
        It can be stopped and started (continued). Nice to use for monitoring tasks.
    """
    def __init__(self, 
                 coro: Callable[[], Coroutine[Any, Any, None]],
                 time_waiting_between_iterations_ms: int = 0, 
                 logger: logging.Logger = logging.getLogger()) -> None:
        self._time_waiting_between_iterations_ms = time_waiting_between_iterations_ms
        self._running: asyncio.Event = asyncio.Event()
        self._coro = coro
        self._daemon: Optional[asyncio.Task] = None
        self._logger = logger
        self._is_stopping = False

    @property
    def running(self) -> asyncio.Event:
        return self._running

    def start(self) -> None:
        assert not self._running.is_set(), "The updater is already running"
        self._running.set()
        self._is_stopping = False
        
        def propagate_task_exception(task):
            if self._is_stopping or not self._running.is_set():
                return
            try:
                # this will raise the exception inside asyncio event loop,
                #  the global exception handler will handle it
                task.result()
            except asyncio.CancelledError:
                pass 

        self._daemon = asyncio.create_task(self._loop())
        self._daemon.add_done_callback(propagate_task_exception)

    async def stop(self) -> None:
        self._running.clear()
        self._is_stopping = True
        if self._daemon is not None:
            daemon = self._daemon
            self._daemon = None
            daemon.cancel()
            with suppress(asyncio.CancelledError):
                await daemon

    @property
    def iteration_interval(self) -> int:
        return self._time_waiting_between_iterations_ms

    @iteration_interval.setter
    def iteration_interval(self, time_waiting_between_iterations_ms: int) -> None:
        self._time_waiting_between_iterations_ms = time_waiting_between_iterations_ms


    async def _loop(self) -> None:
        try:
            while self._running.is_set():
                await self._coro()
                if self._time_waiting_between_iterations_ms > 0:
                    await asyncio.sleep(self._time_waiting_between_iterations_ms / 1000)
        except asyncio.CancelledError:
            raise
        except Exception:
            self._logger.exception("Updater background task crashed")
            raise
        
