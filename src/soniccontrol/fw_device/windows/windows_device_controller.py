import logging

from soniccontrol.communication.connection import Connection, SerialConnection
from soniccontrol.fw_device.device_controller import DeviceController
from soniccontrol.fw_device.fw_device_info import FwDeviceInfo


class WindowsDeviceController(DeviceController):
    def __init__(self, device_info: FwDeviceInfo, logger: logging.Logger):
        self._device_info = device_info
        self._logger = logger
    
    async def create_connection(self, baudrate: int = 9600) -> Connection: 
        assert self._device_info.device_path, "The device has no device path set"
        return SerialConnection(self._device_info.sys_name, self._device_info.device_path, baudrate)


    async def force_into_boot_mode(self) -> FwDeviceInfo:
        ...