import abc
from soniccontrol.communication.connection import Connection
from soniccontrol.fw_device.fw_device_info import FwDeviceInfo


class DeviceController(abc.ABC):
    @abc.abstractmethod
    async def create_connection(self, baudrate: int = 9600) -> Connection: 
        ...

    @abc.abstractmethod
    async def force_into_boot_mode(self) -> FwDeviceInfo:
        """
            Forces the device into bootmode. Also mounts it afterwards.

            Note
            ====
                There should be no active connection, when calling this method.
                As this will invalidate any connections and lead to bugs.

            Returns
            =======
            FwDeviceInfo:
                the info object about the new in boot mode connected device
        """
        ...
