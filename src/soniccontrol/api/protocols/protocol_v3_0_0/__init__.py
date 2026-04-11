from __future__ import annotations

import sys
from importlib import import_module
from typing import Any

_COMMANDS_MODULE = import_module("sonic_protocol.protocols.protocol_v3_0_0.commands.commands")
sys.modules[__name__ + ".commands"] = _COMMANDS_MODULE

__all__ = ["Loglevel", "commands", "get_logger_list_item", "get_logger_list_size", "set_log_level_v3_0_0"]


def __getattr__(name: str) -> Any:
	if name == "commands":
		return _COMMANDS_MODULE

	return getattr(_COMMANDS_MODULE, name)


def __dir__() -> list[str]:
	return sorted(set(__all__) | set(dir(_COMMANDS_MODULE)))