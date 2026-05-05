

import abc
from pathlib import Path
from typing import List

from soniccontrol.fw_device.fw_device_info import FwDeviceInfo


class DeviceDiscovery(abc.ABC):
    @abc.abstractmethod
    async def list_fw_device_infos(
        self,
        include_ttys: bool = True,
        include_disks: bool = True,
        include_unverified_ttys: bool = False,
    ) -> List[FwDeviceInfo]:
        ...

    @abc.abstractmethod
    async def wait_for_device_redetection(self, device_info: FwDeviceInfo, timeout_s: float = 10) -> FwDeviceInfo:
        ...

    async def list_fw_device_names(
        self,
        include_ttys: bool = True,
        include_disks: bool = True,
        include_unverified_ttys: bool = False,
    ) -> List[str]:
        return [
            device.display_name
            for device in await self.list_fw_device_infos(
                include_ttys,
                include_disks,
                include_unverified_ttys,
            )
        ]
    
    async def get_fw_device_info_of(self, device_path: Path | str):
        """
            Returns the firmware device info for a device that is present on the given device_path.

            Returns
            =======
                If no device was detected on the given device_path, it returns None, else FwDeviceInfo
        """
        if isinstance(device_path, Path):
            device_path = str(device_path)

        dev_info = next((
            dev_info for dev_info in await self.list_fw_device_infos()
            if dev_info.device_path == device_path
        ), None)
        return dev_info
        
