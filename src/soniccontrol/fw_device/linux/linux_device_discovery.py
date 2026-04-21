import asyncio
from pathlib import Path
from typing import Any, Generator, Iterable, List, Optional, Set

import attrs
import psutil
import pyudev

from soniccontrol.fw_device.device_discovery import DeviceDiscovery
from soniccontrol.fw_device.fw_device_info import FwDeviceInfo


PICO_VENDOR = "Raspberry_Pi"
PICO_MODELS = {"RPI-RP2", "Pico", "RP2_Boot"}


@attrs.define(hash=True)
class PyudevDeviceQuery:
    subsystem: Optional[str]
    device_type: Optional[str]


def _iter_descendants(dev: pyudev.Device) -> Generator[pyudev.Device, Any, None]:
    for child in dev.children:
        yield child
        yield from _iter_descendants(child)


def _get_descendant_device(
    dev: pyudev.Device,
    queries: Iterable[PyudevDeviceQuery]
) -> Optional[pyudev.Device]:
    assert dev.device_type == "usb_device", "The device passed needs to be a usb device"
    for descendant in _iter_descendants(dev):
        for query in queries:
            if descendant.subsystem == query.subsystem and descendant.device_type == query.device_type:
                return descendant
    return None


def _get_usb_device(dev: pyudev.Device) -> Optional[pyudev.Device]:
    if dev.subsystem == "usb" and dev.device_type == "usb_device":
        return dev
    return dev.find_parent(subsystem="usb", device_type="usb_device")


def _get_mountpoint_of_partition(dev: pyudev.Device) -> Optional[Path]:
    assert dev.subsystem == "block" and dev.device_type == "partition", (
        "The device passed needs to be a block device of type partition"
    )
    for part in psutil.disk_partitions(all=True):
        if part.device == dev.device_node:
            return Path(part.mountpoint)
    return None


def _is_pico_usb_device(dev: pyudev.Device) -> bool:
    return dev.get("ID_VENDOR") == PICO_VENDOR and dev.get("ID_MODEL") in PICO_MODELS


def _get_usb_model(usb_device: pyudev.Device) -> str | None:
    return usb_device.get("ID_MODEL_FROM_DATABASE") or usb_device.get("ID_MODEL") or usb_device.get("PRODUCT")


def _get_device_info(dev: pyudev.Device) -> FwDeviceInfo:
    assert dev.device_node
    assert dev.subsystem
    usb_device = _get_usb_device(dev)
    assert usb_device is not None
    usb_model = _get_usb_model(usb_device)
    usb_sys_name = usb_device.sys_name
    mount_point = None
    if dev.subsystem == "block" and dev.device_type == "disk":
        partition_device = _get_descendant_device(usb_device, [PyudevDeviceQuery("block", "partition")]) if usb_device else None
        if partition_device is not None:
            mount = _get_mountpoint_of_partition(partition_device)
            mount_point = str(mount) if mount is not None else None
    elif dev.subsystem == "block" and dev.device_type == "partition":
        mount = _get_mountpoint_of_partition(dev)
        mount_point = str(mount) if mount is not None else None

    return FwDeviceInfo(
        sys_name=dev.sys_name,
        subsystem=dev.subsystem,
        usb_model=usb_model,
        usb_sys_name=usb_sys_name,
        device_path=dev.device_node,
        mount_point=mount_point,
    )


def _list_pico_usb_devices() -> List[pyudev.Device]:
    context = pyudev.Context()
    pico_usb_devices: List[pyudev.Device] = []
    for usb_device in context.list_devices(subsystem="usb"):
        if _is_pico_usb_device(usb_device):
            pico_usb_devices.append(usb_device)
    return pico_usb_devices


def _list_pico_devices(queries: Iterable[PyudevDeviceQuery]) -> List[pyudev.Device]:
    devices: List[pyudev.Device] = []
    for usb_dev in _list_pico_usb_devices():
        child = _get_descendant_device(usb_dev, queries)
        if child is not None:
            devices.append(child)
    return devices


def _list_pico_tty_devices() -> List[pyudev.Device]:
    return _list_pico_devices([PyudevDeviceQuery("tty", None)])


def _list_usb_tty_devices() -> List[pyudev.Device]:
    context = pyudev.Context()
    devices: List[pyudev.Device] = []
    seen_sys_paths: Set[str] = set()
    for tty_device in context.list_devices(subsystem="tty"):
        if not tty_device.device_node:
            continue
        usb_device = _get_usb_device(tty_device)
        if usb_device is None:
            continue
        if tty_device.sys_path in seen_sys_paths:
            continue
        seen_sys_paths.add(tty_device.sys_path)
        devices.append(tty_device)
    return devices


class LinuxDeviceDiscovery(DeviceDiscovery):
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
            for dev in _list_pico_tty_devices():
                _add_device(_get_device_info(dev))

            if include_unverified_ttys:
                for dev in _list_usb_tty_devices():
                    _add_device(_get_device_info(dev))

        if include_disks:
            queries = {PyudevDeviceQuery("block", "disk")}
            for dev in _list_pico_devices(queries):
                _add_device(_get_device_info(dev))

        return list(devices_by_key.values())

    async def wait_for_device_redetection(self, device_info: FwDeviceInfo) -> FwDeviceInfo:
        assert device_info.usb_sys_name is not None, "The usb_sys_name must be set on the device"
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem="usb")

        seen_remove = False

        usb_device = None
        for device in iter(monitor.poll, None):
            if device.sys_name != device_info.usb_sys_name:
                continue

            action = device.action

            if action == "remove":
                seen_remove = True
            elif action == "add" and seen_remove:
                usb_device = device
                break
            
            await asyncio.sleep(0.5)
    
        await asyncio.sleep(0.5) # wait for enumeration of children
        device = _get_descendant_device(usb_device, [
            PyudevDeviceQuery("tty", None), 
            PyudevDeviceQuery("block", "disk")
        ])
        assert device is not None, "usb device added, but no tty or block device detected"
        return _get_device_info(device)
        

