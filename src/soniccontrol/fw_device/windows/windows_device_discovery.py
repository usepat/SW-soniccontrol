
from typing import List

from soniccontrol.fw_device.device_discovery import DeviceDiscovery
from soniccontrol.fw_device.fw_device_info import FwDeviceInfo


from typing import Dict, Optional
import psutil
import attrs
import serial.tools.list_ports as list_ports
import wmi

from soniccontrol.fw_device.windows.windows_api import get_device_instance_id_from_com_port, get_physical_location_path_of_device

RASPBERRY_PI_USB_VID = 0x2E8A
PICO_MODEL_MARKERS = ("RPI-RP2", "RP2", "PICO")
BOOT_VOLUME_LABELS = {"RPI-RP2", "RP2BOOT", "PICO"}


def _normalized(value: Optional[str]) -> str:
    return (value or "").strip().upper().replace("_", "-")


def _contains_pico_marker(*values: Optional[str]) -> bool:
    normalized_values = [_normalized(value) for value in values if value]
    return any(any(marker in value for marker in PICO_MODEL_MARKERS) for value in normalized_values)


def _logical_drive_path(device_id: str) -> str:
    return f"{device_id}\\"


def _resolve_usb_sys_name_for_disk(pnp_device_id: str) -> str:
    try:
        return get_physical_location_path_of_device(pnp_device_id)
    except AssertionError:
        # USB mass storage devices may not expose a USB\VID_* ancestor in our current lookup.
        # Keep the disk discoverable by falling back to the stable PNP id.
        return pnp_device_id


def _resolve_usb_sys_name_for_port(port) -> str:
    dev_inst = get_device_instance_id_from_com_port(port.name)
    if dev_inst is not None:
        try:
            return get_physical_location_path_of_device(dev_inst)
        except AssertionError:
            pass

    serial_number = getattr(port, "serial_number", None)
    if serial_number:
        return f"USB_SERIAL:{serial_number}"

    hwid = getattr(port, "hwid", None)
    if hwid:
        return f"USB_HWID:{hwid}"

    return f"USB_PORT:{port.name}"

@attrs.define()
class DriveInfo:
    drive_id: str
    pnp_device_id: str # The plug and play id is also the device instance id, we can use to find the parent usb device
    model: str | None
    volume_name: str | None


def _safe_wmi_disks(connection) -> List[object]:
    try:
        return list(connection.Win32_DiskDrive())
    except Exception:
        return []


def _safe_logical_disks_for_wmi_disk(disk, pnp_device_id: str) -> List[object]:
    logical_disks: List[object] = []
    try:
        partitions = list(disk.associators("Win32_DiskDriveToDiskPartition"))
    except Exception:
        return logical_disks

    for partition in partitions:
        try:
            logical_disks.extend(partition.associators("Win32_LogicalDiskToPartition"))
        except Exception:
            pass

    return logical_disks


def _build_drive_mapping() -> Dict[str, DriveInfo]:
    connection = wmi.WMI()
    drive_mapping: Dict[str, DriveInfo] = {}
    for disk in _safe_wmi_disks(connection):
        model: str | None = getattr(disk, "Model", None)
        caption: str | None = getattr(disk, "Caption", None)
        pnp_device_id: str = getattr(disk, "PNPDeviceID")
        is_pico_disk = "VID_2E8A" in pnp_device_id or _contains_pico_marker(model, caption)

        logical_disks = _safe_logical_disks_for_wmi_disk(disk, pnp_device_id)

        for logical_disk in logical_disks:
            drive_id: str | None = getattr(logical_disk, "DeviceID", None)
            volume_name: str | None = getattr(logical_disk, "VolumeName", None)
            if drive_id is None:
                continue
            if is_pico_disk or _normalized(volume_name) in BOOT_VOLUME_LABELS:
                drive_mapping[drive_id] = DriveInfo(drive_id, pnp_device_id, model, volume_name)
    return drive_mapping


class WindowsDeviceDiscovery(DeviceDiscovery):
    async def list_fw_device_infos(
        self,
        include_ttys: bool = True,
        include_disks: bool = True,
        include_unverified_ttys: bool = True,
    ) -> List[FwDeviceInfo]:
        devices_by_key: dict[tuple[str, str], FwDeviceInfo] = {}

        def _add_device(device: FwDeviceInfo) -> None:
            devices_by_key[(device.subsystem, device.sys_name)] = device

        if include_ttys:
            for device in self._list_serial_devices(include_unverified_ttys=include_unverified_ttys):
                _add_device(device)
        if include_disks:
            for device in self._list_boot_disks():
                _add_device(device)
        return list(devices_by_key.values())
    

    def _list_serial_devices(self, include_unverified_ttys: bool = True) -> List[FwDeviceInfo]:
        devices: List[FwDeviceInfo] = []
        for port in list_ports.comports():
            is_pico = port.vid == RASPBERRY_PI_USB_VID or _contains_pico_marker(
                getattr(port, "manufacturer", None),
                getattr(port, "product", None),
                getattr(port, "description", None),
                getattr(port, "hwid", None),
            )

            if not is_pico and not include_unverified_ttys:
                continue

            usb_sys_name = _resolve_usb_sys_name_for_port(port)

            usb_model: str | None = getattr(port, "product", None) or getattr(port, "description", None)
            device_path = port.device
            devices.append(
                FwDeviceInfo(
                    sys_name=port.name,
                    subsystem="tty",
                    usb_model=usb_model,
                    usb_sys_name=usb_sys_name,
                    device_path=device_path,
                )
            )
        return devices
    
    def _list_boot_disks(self) -> List[FwDeviceInfo]:
        partitions = {partition.device.rstrip("\\"): partition for partition in psutil.disk_partitions(all=False)}
        devices: List[FwDeviceInfo] = []
        for drive_id, info in _build_drive_mapping().items():
            partition = partitions.get(drive_id)
            mount_point = partition.mountpoint if partition is not None else _logical_drive_path(drive_id)
            usb_model = info.volume_name or info.model
            usb_sys_name = _resolve_usb_sys_name_for_disk(info.pnp_device_id)
            devices.append(
                FwDeviceInfo(
                    sys_name=drive_id,
                    subsystem="block",
                    usb_sys_name=usb_sys_name,
                    device_path=_logical_drive_path(drive_id),
                    usb_model=usb_model,
                    mount_point=mount_point,
                )
            )
        return devices


