import abc
from enum import Enum, IntEnum
from typing import Any, TypeVar
import numpy as np

from sonic_protocol.defs import ConverterType, Timestamp, Version


class Converter(abc.ABC):
    @abc.abstractmethod
    def validate_val(self, value: Any) -> bool: ...

    @abc.abstractmethod
    def convert_val_to_str(self, value: Any) -> str: ...

    @abc.abstractmethod
    def validate_str(self, text: str) -> bool: ...

    @abc.abstractmethod
    def convert_str_to_val(self, text: str) -> Any: ...


class SignalConverter(Converter):
    def validate_val(self, value: Any) -> bool:
        return isinstance(value, bool)

    def convert_val_to_str(self, value: Any) -> str: 
        assert(self.validate_val(value))
        return "ON" if value else "OFF"

    def validate_str(self, text: str) -> bool: 
        return text.lower() in ["false", "true", "on", "off"]

    def convert_str_to_val(self, text: str) -> Any:
        assert(self.validate_str(text))
        return text.lower() in ["true", "on"]
    
class TerminationConverter(Converter):
    def validate_val(self, value: Any) -> bool: 
        return isinstance(value, bool)

    def convert_val_to_str(self, value: Any) -> str: 
        assert(self.validate_val(value))
        return "activated" if value else "deactivated"
    
    def validate_str(self, text: str) -> bool: 
        return "activated" in text or "deactivated" in text

    def convert_str_to_val(self, text: str) -> Any:
        assert(self.validate_str(text))
        return "activated" in text

class VersionConverter(Converter):
    def validate_val(self, value: Any) -> bool:
        return isinstance(value, Version)

    def convert_val_to_str(self, value: Any) -> str:
        assert (self.validate_val(value))
        return str(value)

    def validate_str(self, text: str) -> bool: 
        try:
            Version.to_version(text)
        except Exception as _:
            return False
        else:
            return True

    def convert_str_to_val(self, text: str) -> Any: 
        assert(self.validate_str(text))
        return Version.to_version(text)

class TimestampConverter(Converter):
    def validate_val(self, value: Any) -> bool:
        return isinstance(value, Timestamp)

    def convert_val_to_str(self, value: Any) -> str:
        assert (self.validate_val(value))
        return str(value)

    def validate_str(self, text: str) -> bool: 
        try:
            Timestamp.to_timestamp(text)
        except Exception as _:
            return False
        else:
            return True

    def convert_str_to_val(self, text: str) -> Any: 
        assert(self.validate_str(text))
        return Timestamp.to_timestamp(text)

class EnumConverter(Converter):
    def __init__(self, target_enum_class: type[Enum]):
        self._target_enum_class: type[Enum] = target_enum_class

    def validate_val(self, value: Any) -> bool: 
        return isinstance(value, self._target_enum_class)

    def convert_val_to_str(self, value: Any) -> str: 
        assert (self.validate_val(value))
        return str(value.value)

    def validate_str(self, text: str) -> bool: 
        return text in [ str(enum_member.value) for enum_member in self._target_enum_class]

    def convert_str_to_val(self, text: str) -> Any: 
        assert(self.validate_str(text))
        if isinstance(self._target_enum_class, IntEnum):
            return self._target_enum_class(int(text))
        return self._target_enum_class(text)

class BuildTypeConverter(Converter):
    def validate_val(self, value: Any) -> bool:
        return isinstance(value, bool)

    def convert_val_to_str(self, value: Any) -> str: 
        assert(self.validate_val(value))
        return "RELEASE" if value else "DEBUG"

    def validate_str(self, text: str) -> bool: 
        return text.lower() in ["release", "debug"]

    def convert_str_to_val(self, text: str) -> Any:
        assert(self.validate_str(text))
        return text.lower() == "release"
    
T = TypeVar("T", int, str, bool, float, np.uint8, np.uint16, np.uint32)
class PrimitiveTypeConverter(Converter):
    def __init__(self, target_class: type[T]):
        self._target_class = target_class

    def validate_val(self, value: Any) -> bool: 
        return isinstance(value, self._target_class)

    def convert_val_to_str(self, value: Any) -> str: 
        assert (self.validate_val(value))
        return str(value)

    def validate_str(self, text: str) -> bool: 
        try:
            if self._target_class is bool:
                lowered = text.strip().lower()
                if lowered in ('true', '1', 'false', '0'):
                    return True
                else:
                    return False
            self._target_class(text)
        except Exception as _:
            return False
        else:
            return True

    def convert_str_to_val(self, text: str) -> Any: 
        if self._target_class is bool:
            lowered = text.strip().lower()
            if lowered in ('true', '1'):
                return True
            else:
                return False
        return self._target_class(text)



def get_converter(converter_type: ConverterType, target_class: Any) -> Converter:
    match converter_type:
        case ConverterType.SIGNAL:
            return SignalConverter()
        case ConverterType.TERMINATION:
            return TerminationConverter()
        case ConverterType.ENUM:
            assert(issubclass(target_class, Enum))
            return EnumConverter(target_class)
        case ConverterType.VERSION:
            return VersionConverter()
        case ConverterType.BUILD_TYPE:
            return BuildTypeConverter()
        case ConverterType.PRIMITIVE:
            return PrimitiveTypeConverter(target_class)
        case ConverterType.TIMESTAMP:
            return TimestampConverter()
