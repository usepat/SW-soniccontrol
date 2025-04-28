

import abc
from enum import Enum
from typing import Any, Dict, Type

from attrs import fields
import attrs

from soniccontrol.interfaces import Scriptable


class ProcedureType(Enum):
    SPECTRUM_MEASURE = "Spectrum Measure"
    RAMP = "Ramp"
    SCAN = "Scan"
    TUNE = "Tune"
    AUTO = "Auto"
    WIPE = "Wipe"

@attrs.define
class ProcedureArgs:
    @classmethod
    def fields_dict_with_alias(cls) -> dict[str, Any]:
        """Converts class fields into a dict using alias names from metadata."""
        result = {}
        for field in fields(cls):
            alias = field.metadata.get("enum", field.name).value
            result[alias] = field
        return result
    
class Procedure(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def get_args_class(cls) -> Type: ...

    @property
    @abc.abstractmethod
    def is_remote(self) -> bool: ...

    @abc.abstractmethod
    async def execute(self, device: Scriptable, args: Any) -> None: ...

    @abc.abstractmethod
    async def fetch_args(self, device: Scriptable) -> Dict[str, Any]: ...
