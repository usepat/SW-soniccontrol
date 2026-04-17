import asyncio
import logging
from pathlib import Path

import pyudev

from soniccontrol.fw_device.fw_device_info import FwDeviceInfo
from soniccontrol.fw_device.linux.linux_device_discovery import (
    LinuxDeviceDiscovery, PyudevDeviceQuery, _get_descendant_device, 
    _get_mountpoint_of_partition, _get_pico_device_info
)
from soniccontrol.utils.cmd import execute_command



class LinuxDeviceController():
    def __init__(self, device_info: FwDeviceInfo, logger: logging.Logger):
        self._device_info = device_info
        self._logger = logger
    
    async def force_into_boot_mode(self) -> FwDeviceInfo:
        context = pyudev.Context()
        assert self._device_info.usb_sys_name is not None
        usb_device = pyudev.Devices.from_name(context, "usb", self._device_info.usb_sys_name)

        tty_device = _get_descendant_device(usb_device, [PyudevDeviceQuery("tty", None)])
        if tty_device is not None:
            assert tty_device.device_node is not None
            await self._reset_pico_over_usb(Path(tty_device.device_node))
            usb_device = pyudev.Devices.from_name(context, sys_name=usb_device.sys_name, subsystem="usb")

        partition_device = _get_descendant_device(usb_device, [PyudevDeviceQuery("block", "partition")])
        assert partition_device is not None, "The usb device has no partition device as child"
        await self._mount_pico(partition_device)
        return _get_pico_device_info(partition_device) 
    
    async def _reset_pico_over_usb(self, device_path: Path) -> None:
        reset_command = f"stty -F {device_path.as_posix()} 1200"
        await execute_command(reset_command, self._logger)
        try:
            self._device_info = await asyncio.wait_for( 
                LinuxDeviceDiscovery().wait_for_device_redetection(self._device_info), 
                5
            )
        except asyncio.TimeoutError:
            pass

    async def _mount_pico(self, partition_dev: pyudev.Device) -> Path:
        assert partition_dev.device_type == "partition", "The device type supplied is not of type partition"

        mountpoint = _get_mountpoint_of_partition(partition_dev)
        if mountpoint is not None:
            self._logger.warning("Partition already mounted")
            return mountpoint
        self._logger.info("No mount point found. Mounting manually")

        try:
            mount_cmd = f"udisksctl mount -b {partition_dev.device_node}"
            result = await execute_command(mount_cmd, self._logger)
            mountpoint = Path(result.split(" at ")[1].strip())
        except Exception:
            mountpoint = Path("/mnt/pico")
            await execute_command(f"sudo mkdir -p {mountpoint}", self._logger)
            await execute_command(f"sudo mount {partition_dev.device_node} {mountpoint}", self._logger)

        mountpoint = _get_mountpoint_of_partition(partition_dev)
        if mountpoint is None:
            raise RuntimeError("Failed to mount Pico")
        self._logger.info("Pico successfully mounted at %s", mountpoint)
        return mountpoint
