
import asyncio
from typing import Any, Literal, Tuple, Union, cast

import attrs
from attrs import validators

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
    def duration_in_ms(self) -> float | int:
        if self.unit == "ms":
            return self.duration
        else:
            return self.duration * 1000
        
    def __sub__(self, other: Union['HolderArgs', float, int]) -> 'HolderArgs':
        """Subtracts another HolderArgs or a duration value and returns a new HolderArgs instance."""
        if isinstance(other, HolderArgs):
            # Convert both durations to milliseconds for calculation
            result_duration_ms = self.duration_in_ms - other.duration_in_ms
        elif isinstance(other, (float, int)):
            # Assume the duration is in the same unit as `self.unit`
            result_duration_ms = self.duration_in_ms - (other * 1000 if self.unit == "s" else other)
        else:
            raise TypeError(f"Unsupported operand type(s) for -: 'HolderArgs' and '{type(other).__name__}'")

        # Ensure the result is non-negative
        result_duration_ms = max(result_duration_ms, 0)

        # Convert back to the original unit of `self`
        if self.unit == "ms":
            return HolderArgs(result_duration_ms, "ms")
        else:
            return HolderArgs(result_duration_ms / 1000, "s")

HoldTuple = Tuple[Union[int, float], TimeUnit]
def convert_to_holder_args(obj: Any) -> HolderArgs:
    if isinstance(obj, tuple) and len(obj) == 2:
        return HolderArgs(*obj)
    elif isinstance(obj, HolderArgs):
        return obj
    elif isinstance(obj, int):
        return HolderArgs(obj, "s")
    else:
        raise TypeError(f"No known conversion from {type(obj)} to {HolderArgs}")

class Holder:
    @staticmethod 
    async def execute(
        args: HolderArgs,
    ) -> None:
        duration = args.duration if args.unit == "s" else args.duration / 1000
        await asyncio.sleep(duration)