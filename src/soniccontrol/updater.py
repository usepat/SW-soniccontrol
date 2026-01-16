
import asyncio
from typing import Optional
from sonic_protocol.schema import DeviceType
from soniccontrol.sonic_device import SonicDevice
from soniccontrol.events import Event, EventManager


class Updater(EventManager):
    UPDATE_EVENT = "update"

    def __init__(self, device: SonicDevice, time_waiting_between_updates_ms: int = 0) -> None:
        super().__init__()
        self._device = device
        self._time_waiting_between_updates_ms = time_waiting_between_updates_ms
        self._running: asyncio.Event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None

    @property
    def running(self) -> asyncio.Event:
        return self._running

    def start(self) -> None:
        self._running.set()
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running.clear()
        if self._task is not None:
            await self._task

    def get_update_interval(self) -> int:
        return self._time_waiting_between_updates_ms

    def set_update_interval(self, time_waiting_between_updates_ms: int) -> None:
        self._time_waiting_between_updates_ms = time_waiting_between_updates_ms

    async def update(self) -> None:
        if self._device.info.device_type == DeviceType.CONFIGURATOR:
            # Configurator does not have update but uses Device so for now I fix it like this
            self._running.clear()
            return 
            
        answer = await self._device.get_update()
        if answer.valid:
            self.emit(Event(Updater.UPDATE_EVENT, status=answer.field_value_dict))
            

    async def _loop(self) -> None:
        try:
            open_connection_flag = self._device.communicator.connection_opened
            while self._running.is_set() and open_connection_flag.is_set():
                await self.update()
                if self._time_waiting_between_updates_ms > 0:
                    await asyncio.sleep(self._time_waiting_between_updates_ms / 1000)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            raise
        
