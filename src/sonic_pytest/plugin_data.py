from enum import Enum, auto
import attrs
from pathlib import Path
from soniccontrol import DeviceType


class Profile(Enum):
    simulation_worker = auto()
    simulation_descale = auto()
    simulation_postman_worker = auto()
    device_worker = auto()
    device_descale = auto()
    device_postman_worker = auto()



@attrs.define()
class SonicControlPlugin:
    is_simulation: bool
    serial_port: str | None
    modbus_serial_port: str | None
    device_type: DeviceType
    simulation_exe_path: Path
    log_path: Path
    remote_server_url: str | None
