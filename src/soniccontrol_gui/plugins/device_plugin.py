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


class WindowFactoryBase(abc.ABC):
    @abc.abstractmethod
    def __call__(self, device: SonicDevice, root: tk.Tk, connection_name: str, **kwargs) -> DeviceWindow:
        ...

class KnownDeviceWindowFactory(WindowFactoryBase):
    def __call__(self, device: SonicDevice, root: tk.Tk, connection_name: str, **kwargs) -> DeviceWindow:
        return KnownDeviceWindow(device, root, connection_name, kwargs.pop("is_legacy_device"))


@attrs.define(hash=True)
class DevicePlugin:
    device_type: DeviceType
    window_factory: WindowFactoryBase
    protocol_factory: ProtocolList


# TODO add UIPluginSlotComponent and PluginSlotRegistry
class UIComponentFactory(abc.ABC):
    @abc.abstractmethod
    def __call__(self, parent: UIComponent, *args, **kwargs) -> UIComponent:
        ...

@attrs.define()
class UIPlugin:
    slot_name: str
    component_factory: UIComponentFactory


class PluginRegistry:
    _registered_plugins: Set[DevicePlugin] = set()

    @staticmethod
    def register_device_plugin(plugin: DevicePlugin):
        PluginRegistry._registered_plugins.add(plugin)

    @staticmethod
    def get_device_plugins() -> List[DevicePlugin]:
        return list(PluginRegistry._registered_plugins)


_operator_protocol_factory = LatestProtocol()

PluginRegistry.register_device_plugin(
    DevicePlugin(DeviceType.MVP_WORKER, KnownDeviceWindowFactory(), _operator_protocol_factory)
)
PluginRegistry.register_device_plugin(
    DevicePlugin(DeviceType.DESCALE, KnownDeviceWindowFactory(), _operator_protocol_factory)
)
PluginRegistry.register_device_plugin(
    DevicePlugin(DeviceType.UNKNOWN, KnownDeviceWindowFactory(), _operator_protocol_factory)
)
PluginRegistry.register_device_plugin(
    DevicePlugin(DeviceType.CRYSTAL, KnownDeviceWindowFactory(), _operator_protocol_factory)
)

def register_device_plugins():
    eps = entry_points()
    for ep in eps.select(group="soniccontrol_gui.plugins"):
        device_plugin = ep.load()
        PluginRegistry.register_device_plugin(device_plugin)