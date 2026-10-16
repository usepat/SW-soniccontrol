from typing import List, Set

import attrs
import abc
import tkinter as tk

from sonic_protocol.protocol import LatestProtocol
from sonic_protocol.schema import DeviceType
from soniccontrol.sonic_device import SonicDevice
from soniccontrol.plugin_discovery import discover_plugins
from soniccontrol_gui.views.core.device_window import DeviceWindow, KnownDeviceWindow

from soniccontrol_gui.views.core.postman_window import PostmanDeviceWindow
from soniccontrol_gui.views.core.diagnostics_window import DiagnosticsWindow



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
    
class DiagnosticsWindowFactory(WindowFactoryBase):
    def __call__(self, device: SonicDevice, root: tk.Tk, connection_name: str, **kwargs) -> DeviceWindow:
        return DiagnosticsWindow(device, root, connection_name)


@attrs.define(hash=True)
class DeviceWindowPlugin:
    """
    A Plugin for a device. It should define how to create the device window and 
    which protocol should be used for communication (configurator uses its completely own protocol.)
    """
    device_type: DeviceType
    window_factory: WindowFactoryBase


class DeviceWindowPluginRegistry:
    _registered_plugins: Set[DeviceWindowPlugin] = set()

    @staticmethod
    def register_plugin(plugin: DeviceWindowPlugin):
        DeviceWindowPluginRegistry._registered_plugins.add(plugin)

    @staticmethod
    def get_plugins() -> List[DeviceWindowPlugin]:
        return list(DeviceWindowPluginRegistry._registered_plugins)



DeviceWindowPluginRegistry.register_plugin(
    DeviceWindowPlugin(DeviceType.MVP_WORKER, KnownDeviceWindowFactory())
)
DeviceWindowPluginRegistry.register_plugin(
    DeviceWindowPlugin(DeviceType.DESCALE, KnownDeviceWindowFactory())
)
DeviceWindowPluginRegistry.register_plugin(
    DeviceWindowPlugin(DeviceType.UNKNOWN, KnownDeviceWindowFactory())
)
DeviceWindowPluginRegistry.register_plugin(
    DeviceWindowPlugin(DeviceType.CRYSTAL, KnownDeviceWindowFactory())
)
DeviceWindowPluginRegistry.register_plugin(
    DeviceWindowPlugin(DeviceType.POSTMAN, PostmanDeviceWindowFactory())
)
DeviceWindowPluginRegistry.register_plugin(
    DeviceWindowPlugin(DeviceType.DIAGNOSTICS_TOOL, DiagnosticsWindowFactory())
)

def register_device_window_plugins():
    group = "soniccontrol_gui.device_window_plugins"

    for plugin in discover_plugins(group):
        DeviceWindowPluginRegistry.register_plugin(plugin)