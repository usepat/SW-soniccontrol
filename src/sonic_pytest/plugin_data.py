from enum import Enum, auto
import attrs
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast
from soniccontrol import DeviceType

if TYPE_CHECKING:
    from _pytest.config import Config


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
    _shared_modbus_device_prepared: bool = attrs.field(default=False, init=False)


class _ConfigWithSonicControlPlugin(Protocol):
    _sonic_control_plugin: SonicControlPlugin


def get_sonic_control_plugin(config: "Config") -> SonicControlPlugin:
    return cast(_ConfigWithSonicControlPlugin, config)._sonic_control_plugin


def modbus_device_preparation_is_required(plugin: SonicControlPlugin, node) -> bool:
    if plugin.is_simulation or plugin.modbus_serial_port is None:
        return False

    if node.get_closest_marker("reprepare_modbus_device") is not None:
        return True

    return not plugin._shared_modbus_device_prepared


def mark_modbus_device_prepared(plugin: SonicControlPlugin) -> None:
    plugin._shared_modbus_device_prepared = True
