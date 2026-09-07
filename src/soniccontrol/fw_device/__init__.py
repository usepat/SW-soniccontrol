from soniccontrol.app_config import PLATFORM, System
from soniccontrol.fw_device.connection import Connection, SerialConnection, CLIConnection, ModbusConnection
from soniccontrol.fw_device.device_discovery import DeviceDiscovery
from soniccontrol.fw_device.fw_device_info import FwDeviceInfo
from soniccontrol.fw_device.remote.remote_device_discovery import RemoteDeviceDiscovery
from soniccontrol.network.connection import RemoteServerConnection


_RESOLVED_DEVICE_INFOS_BY_PATH: dict[tuple[str | None, str], FwDeviceInfo] = {}


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
    # modbus is not yet supported for remote server connection
    # so we have to pop it from kwargs, before we pass kwargs to the constructor
    is_modbus = kwargs.pop("is_modbus", False)
    if dev_info.is_remote:
        assert dev_info.remote_server_url is not None
        return RemoteServerConnection(dev_info.sys_name, dev_info, dev_info.remote_server_url, dev_info.sys_name, baudrate=baudrate, **kwargs)
    if is_modbus:
        return ModbusConnection(dev_info.sys_name, dev_info, dev_info.device_path, baudrate)
    assert dev_info.device_path, "The device has no device path set"
    return SerialConnection(dev_info.sys_name, dev_info, dev_info.device_path, baudrate)


async def resolve_current_device_info(
    device_path: str,
    server_url: str | None = None,
) -> FwDeviceInfo:
    discovery = create_device_discovery(server_url)
    dev_infos = await discovery.list_fw_device_infos(include_unverified_ttys=True)

    dev_info = next((dev for dev in dev_infos if dev.device_path == device_path), None)
    if dev_info is None:
        cached_dev_info = _RESOLVED_DEVICE_INFOS_BY_PATH.get((server_url, device_path))
        if cached_dev_info is not None:
            dev_info = next(
                (
                    dev
                    for dev in dev_infos
                    if dev.usb_sys_name == cached_dev_info.usb_sys_name
                ),
                None,
            )

    assert dev_info is not None, f"No device detected for path {device_path}"
    _RESOLVED_DEVICE_INFOS_BY_PATH[(server_url, device_path)] = dev_info
    return dev_info


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

    if isinstance(connection, ModbusConnection):
        assert new_dev_info.device_path, "The device has no device path set"
        return ModbusConnection(
            f"modbus:{new_dev_info.device_path}",
            new_dev_info,
            new_dev_info.device_path,
            baudrate=connection.baudrate,
            parity=connection.parity,
        )

    baudrate = 9600
    if isinstance(connection, SerialConnection):
        baudrate = connection.baudrate

    return create_connection_to_device(new_dev_info, baudrate)
