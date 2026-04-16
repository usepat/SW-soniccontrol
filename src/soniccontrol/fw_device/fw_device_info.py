from typing import Optional

import attrs


@attrs.define(frozen=True)
class FwDeviceInfo:
    """
    Describes a device that is plugged into the machine or a remote machine.

    Attributes
    ==========
    sys_name: str
        On Linux describes the sys_name of the port the device is connected to. For example sda.

    usb_sys_name: str
        Describes the identifier of the physical usb port on the machine. 
        This is needed, because on boot the device reconnects and can be assigned to a different virtual port.

    subsystem: str
        Used to describe if it is a block, usb, tty or partition device. We use this for pyudev mainly.

    device_path: str
        On linux this is the path to the device node file (basically a handle), used to interact with it.

    mount_point: str | None
        On linux this is the path where the filesystem of the device is integrated.

    remote_server_url: str | None
        Tells if this device is plugged into the local machine or at some remote server

    usb_model: str | None
        Should be RPI-RP2 or Pico_boot. Used for displaying
    """
    sys_name: str
    subsystem: str
    usb_sys_name: str
    device_path: str
    usb_model: Optional[str] = None
    mount_point: Optional[str] = None
    remote_server_url: str | None = None

    @property
    def is_remote(self) -> bool:
        return self.remote_server_url is not None

    @property
    def device_display_name(self) -> str:
        if not self.usb_model:
            return self.sys_name
        return f"{self.usb_model} ({self.sys_name})"
