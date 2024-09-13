
import asyncio
from typing import Optional
from sonicpackage.sonicamp_ import SonicAmp
from sonicpackage.events import Event, EventManager


class Updater(EventManager):
    def __init__(self, device: SonicAmp) -> None:
        super().__init__()
        self._device = device
        self._running: asyncio.Event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None

    @property
    def running(self) -> asyncio.Event:
        return self._running

    def start(self) -> None:
        self._running.set()
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        assert self._task is not None
        self._running.clear()
        await self._task

    async def update(self) -> None:
        # HINT: If ever needed to update different device attributes, we can do that, by checking what components the device has
        # and then additionally call other commands to get this information
        await self._device.execute_command("-", should_log=False)
        self.emit(Event("update", status=self._device.status))

    async def _loop(self) -> None:
        try:
            while self._running.is_set():
                await self.update()
        except Exception as e:
            raise
        
