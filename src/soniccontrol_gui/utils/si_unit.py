
from typing import Any, Generic, TypeVar, cast
import attrs
import cattrs
from sonic_protocol.schema import SIUnit, SIPrefix



@attrs.define(auto_attribs=True, frozen=True)
class SIVarMeta:
    si_unit: SIUnit
    si_prefix_min: SIPrefix
    si_prefix_max: SIPrefix


T = TypeVar("T", int, float)
@attrs.define(auto_attribs=True)
class SIVar(Generic[T]):
    value: T = attrs.field()
    si_prefix: SIPrefix = attrs.field()
    meta: SIVarMeta = attrs.field()

    def allowed_prefix(self, prefix: SIPrefix) -> bool:
        return self.meta.si_prefix_min <= prefix <= self.meta.si_prefix_max

    def to_prefix(self, prefix: SIPrefix):
        if not self.allowed_prefix(prefix):
            raise ValueError("Prefix outside specified limits")
        result = float(self.value) * (self.si_prefix.factor / prefix.factor)
        # Only convert back to int if original was int AND result is a whole number
        if isinstance(self.value, int) and result.is_integer():
            return int(result)
        return type(self.value)(result)

    def convert_to_prefix(self, prefix: SIPrefix):
        if not self.allowed_prefix(prefix):
            raise ValueError("Prefix outside specified limits")
        result = float(self.value) * (self.si_prefix.factor / prefix.factor)
        # Only convert back to int if original was int AND result is a whole number
        if isinstance(self.value, int) and result.is_integer():
            self.value = cast(T, int(result))
        else:
            self.value = cast(T, type(self.value)(result))
        self.si_prefix = prefix
        

    def __attrs_post_init__(self) -> None:
        if not isinstance(self.value, (int, float)) or isinstance(self.value, bool):
            raise TypeError("SIUnit.value must be int|float (no bool)")
        # validate that current prefix is within min/max range
        if  not self.allowed_prefix(self.si_prefix):
            raise ValueError("si_prefix outside allowed range")