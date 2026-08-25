

import abc
import asyncio
from pathlib import Path
from typing import List

from soniccontrol.fw_device.fw_device_info import FwDeviceInfo


class DeviceDiscovery(abc.ABC):
    @abc.abstractmethod
    async def list_fw_device_infos(
        self,
        include_ttys: bool = True,
        include_disks: bool = True,
        include_unverified_ttys: bool = True,
    ) -> List[FwDeviceInfo]:
        ...

    async def wait_for_device_to_appear(self, usb_sys_name: str) -> FwDeviceInfo:
        while True:
            pico_device = await self.get_fw_device_info_via_usb_sys_name(usb_sys_name)
            if pico_device:
                return pico_device
            
            await asyncio.sleep(0.5)

    async def wait_for_device_to_disappear(self, usb_sys_name: str) -> None:
        while True:
            pico_device = await self.get_fw_device_info_via_usb_sys_name(usb_sys_name)
            if pico_device is None:
                return
            
            await asyncio.sleep(0.5)

    async def wait_for_device_redetection(self, device_info: FwDeviceInfo, timeout_s: float = 20) -> FwDeviceInfo:
        async def _redetect():
            await self.wait_for_device_to_disappear(device_info.usb_sys_name)
            return await self.wait_for_device_to_appear(device_info.usb_sys_name)

        return await asyncio.wait_for(_redetect(), timeout_s)
        

    async def list_fw_device_names(
        self,
        include_ttys: bool = True,
        include_disks: bool = True,
        include_unverified_ttys: bool = True,
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
            dev_info for dev_info in await self.list_fw_device_infos(include_unverified_ttys=True)
            if dev_info.device_path == device_path
        ), None)
        return dev_info

    async def get_fw_device_info_via_usb_sys_name(self, usb_sys_name: str):
        """
            Returns the firmware device info for a device that is registered under the usb_sys_name.

            Returns
            =======
                If no corresponding device was found, then it returns None, else FwDeviceInfo
        """
        dev_info = next((
            dev_info for dev_info in await self.list_fw_device_infos(include_unverified_ttys=True)
            if dev_info.usb_sys_name == usb_sys_name
        ), None)
        return dev_info
        
