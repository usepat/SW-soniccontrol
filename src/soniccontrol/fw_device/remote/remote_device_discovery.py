import asyncio
from typing import List

from soniccontrol.fw_device.device_discovery import DeviceDiscovery
from soniccontrol.fw_device.fw_device_info import FwDeviceInfo
from soniccontrol.network.client import RemoteClient


class RemoteDeviceDiscovery(DeviceDiscovery):
    def __init__(self, server_url: str):
        self._server_url = server_url

    async def list_fw_device_infos(
        self,
        include_ttys: bool = True,
        include_disks: bool = True,
        include_unverified_ttys: bool = False,
    ) -> List[FwDeviceInfo]:
        async with RemoteClient(self._server_url) as client:
            return await client.get_devices(include_ttys, include_disks, include_unverified_ttys)

    async def wait_for_device_redetection(self, device_info: FwDeviceInfo, timeout_s: float = 10) -> FwDeviceInfo:
        """
        Params
        ======
        timeout_s: 
            has to be greater than the timeout used on the server to detect devices.
            Else it can be that the client timeout finishes before the server.
        """
        async with RemoteClient(self._server_url) as client:
            return await asyncio.wait_for(client.wait_for_device_redetection(device_info), timeout_s)

