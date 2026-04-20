

import abc
from typing import List

from soniccontrol.fw_device.fw_device_info import FwDeviceInfo


class DeviceDiscovery(abc.ABC):
    @abc.abstractmethod
    async def list_fw_device_infos(self, include_ttys: bool = True, include_disks: bool = True) -> List[FwDeviceInfo]:
        ...

    @abc.abstractmethod
    async def wait_for_device_redetection(self, device_info: FwDeviceInfo) -> FwDeviceInfo:
        ...