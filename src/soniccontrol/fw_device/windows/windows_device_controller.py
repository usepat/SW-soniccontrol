import asyncio
import logging

import serial

from soniccontrol.communication.connection import Connection, SerialConnection
from soniccontrol.fw_device.device_controller import DeviceController
from soniccontrol.fw_device.fw_device_info import FwDeviceInfo
from soniccontrol.fw_device.windows.windows_device_discovery import WindowsDeviceDiscovery


class WindowsDeviceController(DeviceController):
    def __init__(self, device_info: FwDeviceInfo, logger: logging.Logger):
        self._device_info = device_info
        self._logger = logger
    
    async def create_connection(self, baudrate: int = 9600) -> Connection: 
        assert self._device_info.device_path, "The device has no device path set"
        return SerialConnection(self._device_info.sys_name, self._device_info.device_path, baudrate)


    async def force_into_boot_mode(self) -> FwDeviceInfo:
        if self._device_info.subsystem == "block":
            mount_point = self._device_info.mount_point or self._device_info.device_path
            if mount_point is None:
                raise RuntimeError("The selected Pico disk has no mount point")
            return self._device_info

        await self._touch_1200_baud()

        device_discovery = WindowsDeviceDiscovery()
        self._device_info = await device_discovery.wait_for_device_redetection(self._device_info)
        return self._device_info
    
    async def _touch_1200_baud(self) -> None:
        if self._device_info.subsystem != "tty":
            raise RuntimeError(f"Subsystem is not tty but '{self._device_info.subsystem}'")

        device_path = self._device_info.device_path
        if device_path is None:
            raise RuntimeError("The selected Pico serial device has no device path")

        self._logger.info("Resetting Pico over serial port %s", device_path)

        def _touch() -> None:
            with serial.Serial(device_path, baudrate=1200, timeout=1, write_timeout=1) as serial_port:
                serial_port.dtr = False
                serial_port.rts = False

        await asyncio.to_thread(_touch)
