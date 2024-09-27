

import abc
from enum import Enum
from typing import Any, Type

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

    @abc.abstractmethod
    async def execute(self, device: Scriptable, args: Any) -> None: ...
