from importlib import metadata
import sys
from typing import Awaitable, Callable, List, Set

import attrs
import abc
import tkinter as tk

from sonic_protocol.protocol_list import ProtocolList
from sonic_protocol.protocol import LatestProtocol
from sonic_protocol.schema import DeviceType
from soniccontrol.sonic_device import SonicDevice
from soniccontrol.fw_device.connection import Connection
from soniccontrol.plugin_discovery import discover_plugins
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.view import View
from soniccontrol_gui.views.core.device_window import DeviceWindow, KnownDeviceWindow
from importlib.metadata import entry_points

from soniccontrol_gui.views.core.postman_window import PostmanDeviceWindow
from soniccontrol_gui.views.core.diagnostics_window import DiagnosticsWindow

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
    
class DiagnosticsWindowFactory(WindowFactoryBase):
    def __call__(self, device: SonicDevice, root: tk.Tk, connection_name: str, **kwargs) -> DeviceWindow:
        return DiagnosticsWindow(device, root, connection_name)


@attrs.define(hash=True)
class DevicePlugin:
    """
    A Plugin for a device. It should define how to create the device window and 
    which protocol should be used for communication (configurator uses its completely own protocol.)
    """
    device_type: DeviceType
    window_factory: WindowFactoryBase
    protocol_factory: ProtocolList


@attrs.define(hash=True)
class StandaloneDevicePlugin:
    """Device-window plugin owning its transport, without a Sonic protocol."""

    connection_mode: str
    connect: Callable[[tk.Tk, "PluginConnection"], Awaitable[DeviceWindow]]


@attrs.define()
class PluginConnection(Connection):
    plugin: StandaloneDevicePlugin = attrs.field()
    channel: int = attrs.field(default=0)

    async def open_connection(self):
        raise NotImplementedError("The device plugin owns its transport")

    async def close_connection(self) -> None:
        # The device window closes its plugin-owned transport.
        return None


class DevicePluginRegistry:
    _registered_plugins: Set[DevicePlugin] = set()
    _standalone_plugins: Set[StandaloneDevicePlugin] = set()

    @staticmethod
    def register_device_plugin(plugin: DevicePlugin | StandaloneDevicePlugin):
        if isinstance(plugin, StandaloneDevicePlugin):
            DevicePluginRegistry._standalone_plugins.add(plugin)
        else:
            DevicePluginRegistry._registered_plugins.add(plugin)

    @staticmethod
    def get_standalone_plugins() -> List[StandaloneDevicePlugin]:
        return list(DevicePluginRegistry._standalone_plugins)

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
DevicePluginRegistry.register_device_plugin(
    DevicePlugin(DeviceType.DIAGNOSTICS_TOOL, DiagnosticsWindowFactory(), _operator_protocol_factory)
)

def register_device_plugins():
    group = "soniccontrol_gui.device_plugins"

    for plugin in discover_plugins(group):
        DevicePluginRegistry.register_device_plugin(plugin)