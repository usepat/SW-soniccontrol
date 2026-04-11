from __future__ import annotations

import sys
from importlib import import_module
from typing import Any

_COMMANDS_MODULE = import_module("sonic_protocol.protocols.protocol_v2_0_0.commands.commands")
sys.modules[__name__ + ".commands"] = _COMMANDS_MODULE

__all__ = ["commands", "get_control_mode", "get_info", "restart_device", "set_control_mode"]


def __getattr__(name: str) -> Any:
	if name == "commands":
		return _COMMANDS_MODULE

	return getattr(_COMMANDS_MODULE, name)


def __dir__() -> list[str]:
	return sorted(set(__all__) | set(dir(_COMMANDS_MODULE)))