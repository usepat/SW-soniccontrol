from importlib import metadata
import sys
from typing import List, Set

import attrs
import abc
import tkinter as tk

from sonic_protocol.protocol_list import ProtocolList
from sonic_protocol.protocol import LatestProtocol
from sonic_protocol.schema import DeviceType
from soniccontrol.sonic_device import SonicDevice
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.view import View
from soniccontrol_gui.views.core.device_window import DeviceWindow, KnownDeviceWindow
from importlib.metadata import entry_points

from soniccontrol_gui.views.core.postman_window import PostmanDeviceWindow

from soniccontrol_gui.constants import _Files


class WindowFactoryBase(abc.ABC):
    @abc.abstractmethod
    def __call__(self, device: SonicDevice, root: tk.Tk, connection_name: str, **kwargs) -> DeviceWindow:
        ...

class KnownDeviceWindowFactory(WindowFactoryBase):
    def __call__(self, device: SonicDevice, root: tk.Tk, connection_name: str, **kwargs) -> DeviceWindow:
        return KnownDeviceWindow(device, root, connection_name, kwargs.pop("is_legacy_device"))

class PostmanDeviceWindowFactory(WindowFactoryBase):
    def __call__(self, device: SonicDevice, root: tk.Tk, connection_name: str, **kwargs) -> DeviceWindow:
        return PostmanDeviceWindow(device, root, connection_name)


@attrs.define(hash=True)
class DevicePlugin:
    device_type: DeviceType
    window_factory: WindowFactoryBase
    protocol_factory: ProtocolList


class DevicePluginRegistry:
    _registered_plugins: Set[DevicePlugin] = set()

    @staticmethod
    def register_device_plugin(plugin: DevicePlugin):
        DevicePluginRegistry._registered_plugins.add(plugin)

    @staticmethod
    def get_device_plugins() -> List[DevicePlugin]:
        return list(DevicePluginRegistry._registered_plugins)


_operator_protocol_factory = LatestProtocol()

DevicePluginRegistry.register_device_plugin(
    DevicePlugin(DeviceType.MVP_WORKER, KnownDeviceWindowFactory(), _operator_protocol_factory)
)
DevicePluginRegistry.register_device_plugin(
    DevicePlugin(DeviceType.DESCALE, KnownDeviceWindowFactory(), _operator_protocol_factory)
)
DevicePluginRegistry.register_device_plugin(
    DevicePlugin(DeviceType.UNKNOWN, KnownDeviceWindowFactory(), _operator_protocol_factory)
)
DevicePluginRegistry.register_device_plugin(
    DevicePlugin(DeviceType.CRYSTAL, KnownDeviceWindowFactory(), _operator_protocol_factory)
)
DevicePluginRegistry.register_device_plugin(
    DevicePlugin(DeviceType.POSTMAN, PostmanDeviceWindowFactory(), _operator_protocol_factory)
)

def register_device_plugins():
    group = "soniccontrol_gui.device_plugins"

    # 1) Built-in / bundled / normally installed entry points
    try:
        for ep in metadata.entry_points().select(group=group):
            DevicePluginRegistry.register_device_plugin(ep.load())
    except Exception:
        # Don't let a broken plugin kill startup
        pass

    # 2) Plugins dropped into ./plugins (wheels unzipped here)
    _Files.PLUGINS.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(_Files.PLUGINS))  # allow importing plugin packages

    for dist in metadata.distributions(path=[str(_Files.PLUGINS)]):
        for ep in dist.entry_points:
            if ep.group == group:
                try:
                    DevicePluginRegistry.register_device_plugin(ep.load())
                except Exception:
                    # log it; ignore bad plugin
                    pass