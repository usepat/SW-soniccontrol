

import abc
from enum import Enum
from typing import Any, Dict, Type

from soniccontrol.interfaces import Scriptable


class ProcedureType(Enum):
    SPECTRUM_MEASURE = "Spectrum Measure"
    RAMP = "Ramp"
    SCAN = "Scan"
    TUNE = "Tune"
    AUTO = "Auto"
    WIPE = "Wipe"

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
