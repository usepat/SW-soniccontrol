
from abc import ABCMeta
from typing import Generic, TypeVar, cast
import attrs
from sonic_protocol.schema import SIUnit, SIPrefix



@attrs.define(auto_attribs=True, frozen=True)
class SIVarMeta:
    si_unit: SIUnit
    si_prefix_min: SIPrefix
    si_prefix_max: SIPrefix


T = TypeVar("T", int, float)

class SIVarMetaClass(ABCMeta):
    """Metaclass for creating SIVar subclasses with fixed metadata."""
    
    def __new__(mcs, name, bases, namespace, **kwargs):
        # Extract si_meta from kwargs if provided
        si_meta = kwargs.pop('si_meta', None)
        
        # Create the class
        cls = super().__new__(mcs, name, bases, namespace)
        
        # If si_meta is provided, store it as a class attribute
        if si_meta is not None:
            setattr(cls, '_si_meta', si_meta)
        
        return cls


@attrs.define(auto_attribs=True)
class SIVar(Generic[T], metaclass=SIVarMetaClass):
    value: T = attrs.field()
    si_prefix: SIPrefix = attrs.field()
    meta: SIVarMeta = attrs.field(default=None)
    
    # Type hint for the metaclass-added attribute (not an attrs field for subclasses)
    _si_meta: SIVarMeta = attrs.field(init=False, repr=False, default=None)

    def __attrs_post_init__(self) -> None:
        # For subclasses with fixed metadata, use the class metadata
        if hasattr(self.__class__, '_si_meta') and self.__class__ is not SIVar:
            self.meta = self.__class__._si_meta
        # For direct SIVar instantiation (e.g., during deserialization), meta must be provided
        elif self.meta is None:
            raise ValueError("meta must be provided for direct SIVar instantiation")
            
        if not isinstance(self.value, (int, float)) or isinstance(self.value, bool):
            raise TypeError("SIVar.value must be int|float (no bool)")
        # validate that current prefix is within min/max range
        if not self.allowed_prefix(self.si_prefix):
            raise ValueError("si_prefix outside allowed range")

    @classmethod
    def __subclasshook__(cls, subclass):
        # Prevent direct instantiation of SIVar in normal code
        if cls is SIVar and subclass is SIVar:
            # Allow during deserialization but warn about direct use
            import inspect
            frame = inspect.currentframe()
            while frame:
                if 'structure' in frame.f_code.co_name or 'converter' in str(frame.f_locals.get('self', '')):
                    return True  # Allow during deserialization
                frame = frame.f_back
            raise TypeError("SIVar is abstract - use specific subclasses like TemperatureSIVar")
        return NotImplemented

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


# Define specific SI variable types with fixed metadata
ATF_META = SIVarMeta(si_unit=SIUnit.HERTZ, si_prefix_min=SIPrefix.NONE, si_prefix_max=SIPrefix.MEGA)

class AtfSiVar(SIVar[int], si_meta=ATF_META):
    """ATF frequency variable with fixed metadata."""
    
    def __init__(self, value: int = 0, si_prefix: SIPrefix = SIPrefix.NONE):
        super().__init__(value=value, si_prefix=si_prefix)

ATT_META = SIVarMeta(si_unit=SIUnit.CELSIUS, si_prefix_min=SIPrefix.MILLI, si_prefix_max=SIPrefix.NONE)# Milli?

class AttSiVar(SIVar[float], si_meta=ATT_META):
    """ATF frequency variable with fixed metadata."""
    
    def __init__(self, value: float = 0.0, si_prefix: SIPrefix = SIPrefix.NONE):
        super().__init__(value=value, si_prefix=si_prefix)

TEMPERATURE_META = SIVarMeta(si_unit=SIUnit.CELSIUS, si_prefix_min=SIPrefix.MILLI, si_prefix_max=SIPrefix.NONE)


class TemperatureSIVar(SIVar[float], si_meta=TEMPERATURE_META):
    """Temperature variable with fixed metadata."""
    
    def __init__(self, value: float = 0.0, si_prefix: SIPrefix = SIPrefix.NONE):
        super().__init__(value=value, si_prefix=si_prefix)

METER_META = SIVarMeta(si_unit=SIUnit.METER, si_prefix_min=SIPrefix.MILLI, si_prefix_max=SIPrefix.NONE)

class MeterSIVar(SIVar[float], si_meta=METER_META):
    """Temperature variable with fixed metadata."""
    
    def __init__(self, value: float = 0.0, si_prefix: SIPrefix = SIPrefix.NONE):
        super().__init__(value=value, si_prefix=si_prefix)
