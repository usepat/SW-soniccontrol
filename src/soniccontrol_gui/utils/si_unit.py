
from abc import ABCMeta
from typing import Generic, TypeVar, cast, Optional
import attrs
from sonic_protocol.schema import SIUnit, SIPrefix



@attrs.define(auto_attribs=True, frozen=True)
class SIVarMeta:
    si_unit: SIUnit
    si_prefix_min: SIPrefix
    si_prefix_max: SIPrefix
    # Range values as tuples of (value, prefix)
    min_value: tuple[float, SIPrefix] = attrs.field(default=(0.0, SIPrefix.NONE))
    max_value: tuple[float, SIPrefix] = attrs.field(default=(1000.0, SIPrefix.NONE))


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
    meta: Optional[SIVarMeta] = attrs.field(default=None)
    
    # Type hint for the metaclass-added attribute (not an attrs field for subclasses)
    _si_meta: SIVarMeta = attrs.field(init=False, repr=False, default=None)

    def __attrs_post_init__(self) -> None:
        # For subclasses with fixed metadata, use the class metadata
        if hasattr(self.__class__, '_si_meta') and self.__class__ is not SIVar:
            self.meta = self.__class__._si_meta
        # For direct SIVar instantiation (e.g., during deserialization or DictFieldView), meta may be None in valid context
        elif self.meta is None:
            import inspect
            frame = inspect.currentframe()
            allow_none = False
            while frame:
                name_global = frame.f_globals.get('__name__')
                if (
                    'structure' in frame.f_code.co_name
                    or 'converter' in str(frame.f_locals.get('self', ''))
                    or 'create_value_field' in frame.f_code.co_name
                    or (name_global is not None and 'DictFieldView' in name_global)
                ):
                    allow_none = True
                    break
                frame = frame.f_back
            if not allow_none:
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
            # Allow during deserialization or from DictFieldView but warn about direct use
            import inspect
            frame = inspect.currentframe()
            while frame:
                # Allow if called from deserialization or DictFieldView context
                name_global = frame.f_globals.get('__name__')
                if (
                    'structure' in frame.f_code.co_name
                    or 'converter' in str(frame.f_locals.get('self', ''))
                    or 'create_value_field' in frame.f_code.co_name
                    or (name_global is not None and 'DictFieldView' in name_global)
                ):
                    return True  # Allow during deserialization or DictFieldView
                frame = frame.f_back
            raise TypeError("SIVar is abstract - use specific subclasses like TemperatureSIVar")
        return NotImplemented

    def allowed_prefix(self, prefix: SIPrefix) -> bool:
        if self.meta is None:
            return True  # Allow all prefixes if meta is None
        return self.meta.si_prefix_min <= prefix <= self.meta.si_prefix_max

    def get_min_value_in_prefix(self, target_prefix: SIPrefix) -> float:
        """Get the minimum allowed value converted to the target prefix."""
        if self.meta is None:
            return float('-inf')  # No lower bound if meta is None
        min_val, min_prefix = self.meta.min_value
        return min_val * (min_prefix.factor / target_prefix.factor)

    def get_max_value_in_prefix(self, target_prefix: SIPrefix) -> float:
        """Get the maximum allowed value converted to the target prefix."""
        if self.meta is None:
            return float('inf')  # No upper bound if meta is None
        max_val, max_prefix = self.meta.max_value
        return max_val * (max_prefix.factor / target_prefix.factor)

    def is_value_in_range(self, value: float, prefix: SIPrefix) -> bool:
        """Check if a value in the given prefix is within the allowed range."""
        min_val = self.get_min_value_in_prefix(prefix)
        max_val = self.get_max_value_in_prefix(prefix)
        return min_val <= value <= max_val

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


TEMPERATURE_META = SIVarMeta(
    si_unit=SIUnit.CELSIUS, 
    si_prefix_min=SIPrefix.MILLI, 
    si_prefix_max=SIPrefix.NONE,
    min_value=(-273.15, SIPrefix.NONE),     # Absolute zero
    max_value=(1000.0, SIPrefix.NONE)       # 1000°C
)

class TemperatureSIVar(SIVar[float], si_meta=TEMPERATURE_META):
    """Temperature variable with fixed metadata."""
    
    def __init__(self, value: float = 20.0, si_prefix: SIPrefix = SIPrefix.NONE):
        super().__init__(value=value, si_prefix=si_prefix)

METER_META = SIVarMeta(
    si_unit=SIUnit.METER, 
    si_prefix_min=SIPrefix.MILLI, 
    si_prefix_max=SIPrefix.NONE,
    min_value=(0.0, SIPrefix.MILLI),      # 0mm
    max_value=(1000.0, SIPrefix.NONE)     # 1000m
)

class MeterSIVar(SIVar[float], si_meta=METER_META):
    """Distance variable with fixed metadata."""
    
    def __init__(self, value: float = 0.0, si_prefix: SIPrefix = SIPrefix.NONE):
        super().__init__(value=value, si_prefix=si_prefix)

FREQUENCY_META = SIVarMeta(
    si_unit=SIUnit.HERTZ, 
    si_prefix_min=SIPrefix.NONE, 
    si_prefix_max=SIPrefix.MEGA,
    min_value=(100000, SIPrefix.NONE),        # 100kHz
    max_value=(10, SIPrefix.MEGA)       # 10MHz
)

class FrequencySIVar(SIVar[int], si_meta=FREQUENCY_META):
    """Frequency variable for home UI with flexible range."""
    
    def __init__(self, value: int = 100000, si_prefix: SIPrefix = SIPrefix.NONE):
        super().__init__(value=value, si_prefix=si_prefix)

GAIN_META = SIVarMeta(
    si_unit=SIUnit.PERCENT, 
    si_prefix_min=SIPrefix.NONE, 
    si_prefix_max=SIPrefix.NONE,  # Only use base unit (no prefix)
    min_value=(0, SIPrefix.NONE),        # 0%
    max_value=(150, SIPrefix.NONE)       # 150%
)

class GainSIVar(SIVar[int], si_meta=GAIN_META):
    """Gain variable for home UI (single prefix - no combobox)."""
    
    def __init__(self, value: int = 0, si_prefix: SIPrefix = SIPrefix.NONE):
        super().__init__(value=value, si_prefix=si_prefix)


class AtfSiVar(SIVar[int], si_meta=FREQUENCY_META):
    """ATF frequency variable with fixed metadata."""
    
    def __init__(self, value: int = 100000, si_prefix: SIPrefix = SIPrefix.NONE):
        super().__init__(value=value, si_prefix=si_prefix)

ATT_META = SIVarMeta(
    si_unit=SIUnit.CELSIUS, 
    si_prefix_min=SIPrefix.MILLI, 
    si_prefix_max=SIPrefix.NONE,
    min_value=(-273.15, SIPrefix.NONE),       # 0°C
    max_value=(1000.0, SIPrefix.NONE)      # 100°C
)

class AttSiVar(SIVar[float], si_meta=ATT_META):
    """ATF frequency variable with fixed metadata."""
    
    def __init__(self, value: float = 20.0, si_prefix: SIPrefix = SIPrefix.NONE):
        super().__init__(value=value, si_prefix=si_prefix)