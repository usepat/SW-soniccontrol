from soniccontrol.app_config import PLATFORM, System
from soniccontrol.fw_device.connection import Connection, SerialConnection, CLIConnection
from soniccontrol.fw_device.device_discovery import DeviceDiscovery
from soniccontrol.fw_device.fw_device_info import FwDeviceInfo
from soniccontrol.fw_device.remote.remote_device_discovery import RemoteDeviceDiscovery
from soniccontrol.network.connection import RemoteServerConnection


def create_device_discovery(server_url: str | None = None) -> DeviceDiscovery:
    if server_url is not None:
        return RemoteDeviceDiscovery(server_url)
    elif PLATFORM == System.WINDOWS:
        from .windows.windows_device_discovery import WindowsDeviceDiscovery
        return WindowsDeviceDiscovery()
    elif PLATFORM == System.LINUX:
        from .linux.linux_device_discovery import LinuxDeviceDiscovery
        return LinuxDeviceDiscovery()
    else:
        assert False, f"Device discovery is not supported for this platform {PLATFORM}"


def create_connection_to_device(dev_info: FwDeviceInfo, baudrate: int = 9600, **kwargs) -> Connection:
    if dev_info.is_remote:
        assert dev_info.remote_server_url is not None
        return RemoteServerConnection(dev_info.sys_name, dev_info, dev_info.remote_server_url, dev_info.sys_name, baudrate=baudrate, **kwargs)
    
    assert dev_info.device_path, "The device has no device path set"
    return SerialConnection(dev_info.sys_name, dev_info, dev_info.device_path, baudrate)


async def redetect_connection(connection: Connection) -> Connection:
    """
    Tries to redetect the connection and gives back a new valid connection class.

    Note
    ====
    This method does not open or close the connection.
    """

    if isinstance(connection, CLIConnection):
        return connection

    dev_info = connection.dev_info
    assert dev_info is not None, "dev_info was not set"
    device_discovery = create_device_discovery(dev_info.remote_server_url)
    new_dev_info = await device_discovery.wait_for_device_redetection(dev_info)
    return create_connection_to_device(new_dev_info)
