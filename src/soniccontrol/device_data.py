from __future__ import annotations

import attrs

from sonic_protocol.schema import DeviceType, Version


@attrs.define(auto_attribs=True)
class FirmwareInfo:
    serial_number: str = attrs.field(default="unknown")
    device_type: DeviceType = attrs.field(default=DeviceType.UNKNOWN)
    hardware_version: Version = attrs.field(default=Version(0, 0, 0), converter=Version.to_version)
    firmware_info: str = attrs.field(default="")
    firmware_version: Version = attrs.field(default=Version(0, 0, 0), converter=Version.to_version) 
    protocol_version: Version = attrs.field(default=Version(0, 0, 0), converter=Version.to_version)
    is_release: bool = attrs.field(default=True)
