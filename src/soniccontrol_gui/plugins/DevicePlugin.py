from typing import Callable, List, Set

import attrs
import abc
import tkinter as tk

from sonic_protocol.protocol_list import ProtocolList, ProtocolType
from sonic_protocol.protocol import LatestProtocol
from sonic_protocol.schema import DeviceType, Protocol
from soniccontrol.sonic_device import SonicDevice
from soniccontrol_gui.views.core.device_window import DeviceWindow, KnownDeviceWindow


class WindowFactoryBase(abc.ABC):
    @abc.abstractmethod
    def __call__(self, device: SonicDevice, root: tk.Tk, connection_name: str, **kwargs) -> DeviceWindow:
        ...

class KnownDeviceWindowFactory(WindowFactoryBase):
    def __call__(self, device: SonicDevice, root: tk.Tk, connection_name: str, **kwargs) -> DeviceWindow:
        return KnownDeviceWindow(device, root, connection_name, kwargs.pop("is_legacy_device"))


class ProtocolFactoryBase(abc.ABC):
    @abc.abstractmethod
    def __call__(self, protocol_type: ProtocolType, **kwargs) -> Protocol:
        ...

class ProtocolFactory(ProtocolFactoryBase):
    def __init__(self, protocol_list: ProtocolList):
        self._protocol_list = protocol_list

    def __call__(self, protocol_type: ProtocolType, **kwargs) -> Protocol:
        return self._protocol_list.build_protocol_for(protocol_type)


@attrs.define(hash=True)
class DevicePlugin:
    device_type: DeviceType
    window_factory: WindowFactoryBase
    protocol_factory: ProtocolFactoryBase

class PluginRegistry:
    _registered_plugins: Set[DevicePlugin] = set()

    @staticmethod
    def register_device_plugin(plugin: DevicePlugin):
        PluginRegistry._registered_plugins.add(plugin)

    @staticmethod
    def get_device_plugins() -> List[DevicePlugin]:
        return list(PluginRegistry._registered_plugins)



_operator_protocol_factory = ProtocolFactory(LatestProtocol())

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
