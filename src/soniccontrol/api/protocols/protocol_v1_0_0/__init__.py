from __future__ import annotations

import sys
from importlib import import_module
from typing import Any

_PROTOCOL_MODULE = import_module("sonic_protocol.protocols.protocol_v1_0_0.protocol_v1_0_0")
sys.modules[__name__ + ".protocol"] = _PROTOCOL_MODULE
protocol = _PROTOCOL_MODULE
get_protocol = _PROTOCOL_MODULE.get_protocol

_SUBMODULE_ALIASES = {
	"communication_fields": "sonic_protocol.protocols.protocol_v1_0_0.communication_commands.communication_fields",
	"descaler_commands": "sonic_protocol.protocols.protocol_v1_0_0.transducer_commands.descaler_commands",
	"flashing_commands": "sonic_protocol.protocols.protocol_v1_0_0.flashing_commands.flashing_commands",
	"generic_commands": "sonic_protocol.protocols.protocol_v1_0_0.generic_commands.generic_commands",
	"generic_fields": "sonic_protocol.protocols.protocol_v1_0_0.generic_commands.generic_fields",
	"procedure_commands": "sonic_protocol.protocols.protocol_v1_0_0.procedure_commands.procedure_commands",
	"procedure_fields": "sonic_protocol.protocols.protocol_v1_0_0.procedure_commands.procedure_fields",
	"transducer_commands": "sonic_protocol.protocols.protocol_v1_0_0.transducer_commands.transducer_commands",
	"transducer_fields": "sonic_protocol.protocols.protocol_v1_0_0.transducer_commands.transducer_fields",
	"transducer_generic_commands": "sonic_protocol.protocols.protocol_v1_0_0.transducer_commands.generic_commands",
	"unknown_commands": "sonic_protocol.protocols.protocol_v1_0_0.unknown_commands.unknown_commands",
}

for _alias, _target in _SUBMODULE_ALIASES.items():
	sys.modules.setdefault(__name__ + f".{_alias}", import_module(_target))

__all__ = ["get_protocol", "protocol"]


def __getattr__(name: str) -> Any:
	if name == "protocol":
		return _PROTOCOL_MODULE

	if name in _SUBMODULE_ALIASES:
		return sys.modules[__name__ + f".{name}"]

	return getattr(_PROTOCOL_MODULE, name)


def __dir__() -> list[str]:
	return sorted(set(__all__) | set(dir(_PROTOCOL_MODULE)))