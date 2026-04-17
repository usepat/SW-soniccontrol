import logging

from soniccontrol.app_config import PLATFORM, System
from soniccontrol.fw_device.device_controller import DeviceController
from soniccontrol.fw_device.device_discovery import DeviceDiscovery
from soniccontrol.fw_device.fw_device_info import FwDeviceInfo


def create_device_discovery(server_url: str | None = None) -> DeviceDiscovery:
    if server_url is not None:
        pass

    if PLATFORM == System.WINDOWS:
        from .windows.windows_device_discovery import WindowsDeviceDiscovery
        return WindowsDeviceDiscovery()
    elif PLATFORM == System.LINUX:
        from .linux.linux_device_discovery import LinuxDeviceDiscovery
        return LinuxDeviceDiscovery()
    else:
        assert False, f"Device discovery is not supported for this platform {PLATFORM}"

def create_device_controller(dev_info: FwDeviceInfo, logger: logging.Logger = logging.getLogger()) -> DeviceController:
    if dev_info.is_remote:
        pass
    
    if PLATFORM == System.WINDOWS:
        from .windows.windows_device_controller import WindowsDeviceController
        return WindowsDeviceController(dev_info, logger)
    elif PLATFORM == System.LINUX:
        from .linux.linux_device_controller import LinuxDeviceController
        return LinuxDeviceController(dev_info, logger)
    else:
        assert False, "No device controller available for this device"
