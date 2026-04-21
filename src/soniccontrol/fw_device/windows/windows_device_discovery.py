
from typing import List

from soniccontrol.fw_device.device_discovery import DeviceDiscovery
from soniccontrol.fw_device.fw_device_info import FwDeviceInfo


from typing import Dict, Optional

import psutil
import attrs
import serial.tools.list_ports as list_ports
import wmi

from soniccontrol.fw_device.windows.device_event_watcher import get_device_event_watcher
from soniccontrol.fw_device.windows.windows_api import get_device_instance_id_from_com_port, get_physical_location_path_of_device, is_there_usb_device_on_location

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

@attrs.define()
class DriveInfo:
    drive_id: str
    pnp_device_id: str # The plug and play id is also the device instance id, we can use to find the parent usb device
    model: str | None
    volume_name: str | None

def _build_drive_mapping() -> Dict[str, DriveInfo]:
    connection = wmi.WMI()
    drive_mapping: Dict[str, DriveInfo] = {}
    for disk in connection.Win32_DiskDrive():
        model: str | None = getattr(disk, "Model", None)
        caption: str | None = getattr(disk, "Caption", None)
        pnp_device_id: str = getattr(disk, "PNPDeviceID")
        is_pico_disk = "VID_2E8A" in pnp_device_id or _contains_pico_marker(model, caption)

        logical_disks = []
        for partition in disk.associators("Win32_DiskDriveToDiskPartition"):
            logical_disks.extend(partition.associators("Win32_LogicalDiskToPartition"))

        for logical_disk in logical_disks:
            drive_id: str | None = getattr(logical_disk, "DeviceID", None)
            volume_name: str | None = getattr(logical_disk, "VolumeName", None)
            if drive_id is None:
                continue
            if is_pico_disk or _normalized(volume_name) in BOOT_VOLUME_LABELS:
                drive_mapping[drive_id] = DriveInfo(drive_id, pnp_device_id, volume_name, model)
    return drive_mapping


class WindowsDeviceDiscovery(DeviceDiscovery):
    async def list_fw_device_infos(
        self,
        include_ttys: bool = True,
        include_disks: bool = True,
        include_unverified_ttys: bool = False,
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


    async def wait_for_device_redetection(self, device_info: FwDeviceInfo) -> FwDeviceInfo:
        event_queue = get_device_event_watcher().event_queue

        last_seen_present = True
        while True:
            await event_queue.get() # wait for device removed or connected event

            # windows does not tell us which device appeared, so we have to scan it by ourself
            is_enumerated = is_there_usb_device_on_location(device_info.usb_sys_name)

            if last_seen_present and not is_enumerated:
                last_seen_present = False

            if not last_seen_present and is_enumerated:
                # device reappeared
                break

        fw_dev_infos = await self.list_fw_device_infos()
        return next(iter([ 
            fw_dev for fw_dev in fw_dev_infos 
            if fw_dev.usb_sys_name == device_info.usb_sys_name
        ]))



    def _list_serial_devices(self, include_unverified_ttys: bool = False) -> List[FwDeviceInfo]:
        devices: List[FwDeviceInfo] = []
        for port in list_ports.comports():
            is_pico = port.vid == RASPBERRY_PI_USB_VID or _contains_pico_marker(
                getattr(port, "manufacturer", None),
                getattr(port, "product", None),
                getattr(port, "description", None),
            )

            if not is_pico and not include_unverified_ttys:
                continue

            dev_inst = get_device_instance_id_from_com_port(port.name)
            if dev_inst is None:
                continue

            try:
                usb_sys_name = get_physical_location_path_of_device(dev_inst)
            except AssertionError:
                continue

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
            devices.append(
                FwDeviceInfo(
                    sys_name=drive_id,
                    subsystem="block",
                    usb_sys_name=get_physical_location_path_of_device(info.pnp_device_id),
                    device_path=_logical_drive_path(drive_id),
                    usb_model=usb_model,
                    mount_point=mount_point,
                )
            )
        return devices