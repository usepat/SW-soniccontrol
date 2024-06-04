
import asyncio
from typing import Optional
from soniccontrol.sonicpackage.sonicamp_ import SonicAmp
from soniccontrol.tkintergui.utils.events import Event, EventManager


class Updater(EventManager):
    def __init__(self, device: SonicAmp) -> None:
        self._device = device
        self._running: asyncio.Event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None

    @property
    def running(self) -> asyncio.Event:
        return self._running


    @property
    def task(self) -> Optional[asyncio.Task]:
        return self._task


    def execute(self, *args, **kwargs) -> None:
        self._task = asyncio.create_task(self._loop())
        self._running.set()


    def stop_execution(self, *args, **kwargs) -> None:
        self._running.clear()


    async def _loop(self) -> None:
        while self._running.is_set():
            await self.worker()


    async def _worker(self) -> None:
        await self._device.get_status()

        # HINT: If ever needed to update different device attributes, we can do that, by checking what components the device has
        # and then additionally call other commands to get this information

        self.emit(Event("update", self._device.status))