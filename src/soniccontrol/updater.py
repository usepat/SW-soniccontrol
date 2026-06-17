
import asyncio
from typing import Optional
from sonic_protocol.schema import DeviceType
from soniccontrol.sonic_device import SonicDevice
from soniccontrol.events import Event, EventManager
from soniccontrol.utils.cyclic_task import CyclicTask

class Updater(EventManager, CyclicTask):
    UPDATE_EVENT = "update"

    def __init__(self, device: SonicDevice, time_waiting_between_updates_ms: int = 0) -> None:
        EventManager.__init__(self)
        CyclicTask.__init__(self, self.update, time_waiting_between_updates_ms, device._logger)
        self._device = device

    async def update(self) -> None:
        is_not_connected = not self._device.communicator.connection_opened.is_set()
        if self._device.info.device_type == DeviceType.CONFIGURATOR or is_not_connected:
            # Configurator does not have update but uses Device so for now I fix it like this
            self.running.clear()
            return 
            
        answer = await self._device.get_update()
        if answer.valid:
            self.emit(Event(Updater.UPDATE_EVENT, status=answer.field_value_dict))

