
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