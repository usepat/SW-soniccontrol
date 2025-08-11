
import asyncio
from typing import Any, Literal, Tuple, Union, cast

import attrs
from attrs import validators
import re

TimeUnit = Literal["ms", "s"]

@attrs.define(auto_attribs=True)
class HolderArgs:
    duration: float | int = attrs.field(default=0., validator=[
        validators.instance_of(float | int),
        validators.ge(0)
    ])
    unit: TimeUnit = cast(
        TimeUnit, 
        attrs.field(factory=lambda: str("ms"), validator=[validators.in_(["ms", "s"])])
    )

    @property
    def duration_in_ms(self) -> float:
        if self.unit == "ms":
            return float(self.duration)
        else:
            return float(self.duration * 1000)
        
    def __str__(self) -> str:
        return f"{self.duration}{self.unit}"

    def __sub__(self, other: Union['HolderArgs', float, int]) -> 'HolderArgs':
        """Subtracts another HolderArgs or a duration value and returns a new HolderArgs instance."""
        if isinstance(other, HolderArgs):
            # Convert both durations to milliseconds for calculation
            result_duration_ms = self.duration_in_ms - other.duration_in_ms
        else:
            raise TypeError(f"Unsupported operand type(s) for -: 'HolderArgs' and '{type(other).__name__}'")

        # Ensure the result is non-negative
        result_duration_ms = max(result_duration_ms, 0)

        # Convert back to the original unit of `self`
        if self.unit == "ms":
            return HolderArgs(result_duration_ms, "ms")
        else:
            return HolderArgs(result_duration_ms / 1000, "s")
        
    @staticmethod
    def to_holder_args(obj: Any) -> "HolderArgs":
        return convert_to_holder_args(obj)

HoldTuple = Tuple[Union[int, float], TimeUnit]
def convert_to_holder_args(obj: Any) -> HolderArgs:
    if isinstance(obj, tuple) and len(obj) == 2:
        return HolderArgs(*obj)
    elif isinstance(obj, str):
        regex = r"(?P<duration>\d+(\.\d+)?) *(?P<unit>(ms)|s)"
        match_result = re.match(regex, obj)
        if match_result is None:
            raise ValueError("The string needs to contain the length of duration followed by an unit [s/ms]")
        duration = float(match_result.group("duration"))
        unit: Literal["s", "ms"] = match_result.group("unit") # type: ignore
        return HolderArgs(duration, unit)
    elif isinstance(obj, HolderArgs):
        return obj
    elif isinstance(obj, int):
        return HolderArgs(obj, "ms")
    else:
        raise TypeError(f"No known conversion from {type(obj)} to {HolderArgs}")

class Holder:
    @staticmethod 
    async def execute(
        args: HolderArgs,
    ) -> None:
        await asyncio.sleep(args.duration_in_ms / 1000)