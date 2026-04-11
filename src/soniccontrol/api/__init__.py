from __future__ import annotations

import sys
from importlib import import_module
from types import ModuleType
from typing import TYPE_CHECKING, Any

import soniccontrol.api.commands as commands

from sonic_protocol.schema import DeviceType
from soniccontrol.api.version import PLUGIN_API_VERSION

_SUBMODULE_ALIASES = {
    "command_codes": "sonic_protocol.command_codes",
    "device": "soniccontrol.sonic_device",
    "field_names": "sonic_protocol.field_names",
    "procedures": "soniccontrol.procedures.procs",
    "protocol": "sonic_protocol.protocol",
    "schema": "sonic_protocol.schema",
    "si_unit": "sonic_protocol.si_unit",
}

_GUI_CONSTANTS_MODULE = "soniccontrol_gui.constants"
_GUI_ANIMATOR_MODULE = "soniccontrol_gui.utils.animator"
_GUI_APP_STATE_MODULE = "soniccontrol_gui.views.core.app_state"
_GUI_DEVICE_WINDOW_MODULE = "soniccontrol_gui.views.core.device_window"
_GUI_VIEW_MODULE = "soniccontrol_gui.view"
_NETWORK_SERVER_MODULE = "soniccontrol.network.server"

_EXPORT_MODULE_ALIASES = {
    "gui": {
        "_Files": (_GUI_CONSTANTS_MODULE, "_Files"),
        "ATConfig": ("soniccontrol_gui.views.configuration.configuration", "ATConfig"),
        "Animator": (_GUI_ANIMATOR_MODULE, "Animator"),
        "AppExecutionContext": (_GUI_APP_STATE_MODULE, "AppExecutionContext"),
        "AppState": (_GUI_APP_STATE_MODULE, "AppState"),
        "DeviceWindow": (_GUI_DEVICE_WINDOW_MODULE, "DeviceWindow"),
        "DeviceWindowView": (_GUI_DEVICE_WINDOW_MODULE, "DeviceWindowView"),
        "DialogOptions": ("soniccontrol_gui.widgets.message_box", "DialogOptions"),
        "DotAnimationSequence": (_GUI_ANIMATOR_MODULE, "DotAnimationSequence"),
        "ExecutionState": (_GUI_APP_STATE_MODULE, "ExecutionState"),
        "FileBrowseButtonView": ("soniccontrol_gui.widgets.file_browse_button", "FileBrowseButtonView"),
        "FormWidget": ("soniccontrol_gui.widgets.form_widget", "FormWidget"),
        "ImageLoader": ("soniccontrol_gui.utils.image_loader", "ImageLoader"),
        "KnownDeviceWindow": (_GUI_DEVICE_WINDOW_MODULE, "KnownDeviceWindow"),
        "Logging": ("soniccontrol_gui.views.control.logging", "Logging"),
        "MessageBox": ("soniccontrol_gui.widgets.message_box", "MessageBox"),
        "SerialMonitor": ("soniccontrol_gui.views.control.serialmonitor", "SerialMonitor"),
        "TabView": (_GUI_VIEW_MODULE, "TabView"),
        "TkinterView": (_GUI_VIEW_MODULE, "TkinterView"),
        "UIComponent": ("soniccontrol_gui.ui_component", "UIComponent"),
        "View": (_GUI_VIEW_MODULE, "View"),
        "enable_all_children": ("soniccontrol_gui.utils.widget_utils", "enable_all_children"),
        "file_dialog_opts": (_GUI_CONSTANTS_MODULE, "file_dialog_opts"),
        "files": (_GUI_CONSTANTS_MODULE, "files"),
        "images": ("soniccontrol_gui.resources", "images"),
        "load_animation": (_GUI_ANIMATOR_MODULE, "load_animation"),
        "sizes": (_GUI_CONSTANTS_MODULE, "sizes"),
        "style": (_GUI_CONSTANTS_MODULE, "style"),
        "ui_labels": (_GUI_CONSTANTS_MODULE, "ui_labels"),
    },
    "network": {
        "HTTP_CLIENT_ERROR": (_NETWORK_SERVER_MODULE, "HTTP_CLIENT_ERROR"),
        "HTTP_OK": (_NETWORK_SERVER_MODULE, "HTTP_OK"),
        "HTTP_SERVER_ERROR": (_NETWORK_SERVER_MODULE, "HTTP_SERVER_ERROR"),
        "ServerPlugin": ("soniccontrol.network.plugin", "ServerPlugin"),
        "execute_in_event_loop": (_NETWORK_SERVER_MODULE, "execute_in_event_loop"),
        "http_ok": (_NETWORK_SERVER_MODULE, "http_ok"),
    },
    "plugins": {
        "DevicePlugin": ("soniccontrol_gui.plugins.device_plugin", "DevicePlugin"),
        "UIComponentFactory": ("soniccontrol_gui.plugins.ui_plugin", "UIComponentFactory"),
        "UIPlugin": ("soniccontrol_gui.plugins.ui_plugin", "UIPlugin"),
        "WindowFactoryBase": ("soniccontrol_gui.plugins.device_plugin", "WindowFactoryBase"),
    },
}


def _create_lazy_alias_module(alias: str, target: str) -> ModuleType:
    module_name = __name__ + f".{alias}"
    module = ModuleType(module_name)
    loaded_module: ModuleType | None = None

    def _load() -> ModuleType:
        nonlocal loaded_module
        if loaded_module is None:
            loaded_module = import_module(target)
        return loaded_module

    def _module_getattr(name: str) -> Any:
        return getattr(_load(), name)

    def _module_dir() -> list[str]:
        return sorted(dir(_load()))

    module.__dict__.update(
        {
            "__doc__": f"Lazy alias for {target}",
            "__getattr__": _module_getattr,
            "__dir__": _module_dir,
        }
    )
    return module


def _create_lazy_export_module(alias: str, exports: dict[str, tuple[str, str]]) -> ModuleType:
    module_name = __name__ + f".{alias}"
    module = ModuleType(module_name)
    loaded_values: dict[str, Any] = {}

    def _load(name: str) -> Any:
        if name not in loaded_values:
            target_module, attribute_name = exports[name]
            loaded_values[name] = getattr(import_module(target_module), attribute_name)
        return loaded_values[name]

    def _module_getattr(name: str) -> Any:
        if name not in exports:
            raise AttributeError(f"module {module_name!r} has no attribute {name!r}")
        return _load(name)

    def _module_dir() -> list[str]:
        return sorted(exports)

    module.__dict__.update(
        {
            "__doc__": f"Lazy export module for {alias}",
            "__all__": sorted(exports),
            "__getattr__": _module_getattr,
            "__dir__": _module_dir,
        }
    )
    return module


for _alias, _target in _SUBMODULE_ALIASES.items():
    sys.modules.setdefault(__name__ + f".{_alias}", _create_lazy_alias_module(_alias, _target))

for _alias, _exports in _EXPORT_MODULE_ALIASES.items():
    sys.modules.setdefault(__name__ + f".{_alias}", _create_lazy_export_module(_alias, _exports))

if TYPE_CHECKING:
    from sonic_protocol.protocol_list import ProtocolList
    from sonic_protocol.protocols.protocol_base.protocol_base import Protocol_base
    from soniccontrol.app_config import APP_CONFIG, PLATFORM, AppConfig, System, get_simulation_exe
    from soniccontrol.communication.connection import SerialConnection
    from soniccontrol.communication.serial_communicator import SerialCommunicator
    from soniccontrol.builder import DeviceBuilder
    from soniccontrol.data_capturing.converter import create_cattrs_converter_for_basic_serialization
    from soniccontrol.events import Event, EventManager, PropertyChangeEvent
    from soniccontrol.network.connection import RemoteServerConnection

__all__ = [
    "APP_CONFIG",
    "AppConfig",
    "DeviceBuilder",
    "PLUGIN_API_VERSION",
    "DeviceType",
    "Event",
    "EventManager",
    "PLATFORM",
    "PropertyChangeEvent",
    "ProtocolList",
    "Protocol_base",
    "SerialConnection",
    "SerialCommunicator",
    "System",
    "RemoteServerConnection",
    "create_cattrs_converter_for_basic_serialization",
    "commands",
    "get_simulation_exe",
]


def __getattr__(name: str) -> Any:
    if name in {"APP_CONFIG", "AppConfig", "PLATFORM", "System", "get_simulation_exe"}:
        from soniccontrol.app_config import APP_CONFIG, PLATFORM, AppConfig, System, get_simulation_exe

        return {
            "APP_CONFIG": APP_CONFIG,
            "AppConfig": AppConfig,
            "PLATFORM": PLATFORM,
            "System": System,
            "get_simulation_exe": get_simulation_exe,
        }[name]

    if name == "DeviceBuilder":
        from soniccontrol.builder import DeviceBuilder

        return DeviceBuilder

    if name in {"Event", "EventManager", "PropertyChangeEvent"}:
        from soniccontrol.events import Event, EventManager, PropertyChangeEvent

        return {
            "Event": Event,
            "EventManager": EventManager,
            "PropertyChangeEvent": PropertyChangeEvent,
        }[name]

    if name in {"ProtocolList", "Protocol_base"}:
        from sonic_protocol.protocol_list import ProtocolList
        from sonic_protocol.protocols.protocol_base.protocol_base import Protocol_base

        return {
            "ProtocolList": ProtocolList,
            "Protocol_base": Protocol_base,
        }[name]

    if name == "SerialConnection":
        from soniccontrol.communication.connection import SerialConnection

        return SerialConnection

    if name == "SerialCommunicator":
        from soniccontrol.communication.serial_communicator import SerialCommunicator

        return SerialCommunicator

    if name == "RemoteServerConnection":
        from soniccontrol.network.connection import RemoteServerConnection

        return RemoteServerConnection

    if name == "create_cattrs_converter_for_basic_serialization":
        from soniccontrol.data_capturing.converter import create_cattrs_converter_for_basic_serialization

        return create_cattrs_converter_for_basic_serialization

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(__all__)