from __future__ import annotations

import sys
from importlib import import_module
from types import ModuleType
from typing import Any

_CONTRACT_GENERATORS_MODULE = import_module("sonic_protocol.protocols.contract_generators")
sys.modules[__name__ + ".contract_generators"] = _CONTRACT_GENERATORS_MODULE

__all__ = ["contract_generators", "create_version_field"]


def __getattr__(name: str) -> Any:
	if name == "contract_generators":
		return _CONTRACT_GENERATORS_MODULE

	return getattr(_CONTRACT_GENERATORS_MODULE, name)


def __dir__() -> list[str]:
	return sorted(set(__all__) | set(dir(_CONTRACT_GENERATORS_MODULE)))