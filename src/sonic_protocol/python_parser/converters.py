import abc
from enum import Enum, IntEnum
from typing import Any, TypeVar
import numpy as np
from base64 import b64decode, b64encode

from sonic_protocol.schema import Timestamp, Version


class Converter(abc.ABC):
    @abc.abstractmethod
    def validate_val(self, value: Any) -> bool: ...

    @abc.abstractmethod
    def convert_val_to_str(self, value: Any) -> str: ...

    @abc.abstractmethod
    def validate_str(self, text: str) -> bool: ...

    @abc.abstractmethod
    def convert_str_to_val(self, text: str) -> Any: ...


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
        return str(value.value).lower()

    def validate_str(self, text: str) -> bool: 
        return text.lower() in [ str(enum_member.value).lower() for enum_member in self._target_enum_class]

    def convert_str_to_val(self, text: str) -> Any: 
        assert(self.validate_str(text))
        if isinstance(self._target_enum_class, IntEnum):
            return self._target_enum_class(int(text))
        # Return the corresponding enum member, case-insensitive match on value or name
        for enum_member in self._target_enum_class:
            if text.lower() == str(enum_member.value).lower() or text.lower() == enum_member.name.lower():
                return enum_member
        raise ValueError(f"No matching enum member found for '{text}' in {self._target_enum_class}")
    
T = TypeVar("T", int, str, bool, float, np.uint8, np.uint16, np.uint32)
class PrimitiveTypeConverter(Converter):
    def __init__(self, target_class: type[T]):
        self._target_class = target_class

    def validate_val(self, value: Any) -> bool: 
        if self._target_class in (np.uint8, np.uint16, np.uint32):
            return isinstance(value, (int, self._target_class))
        
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
        
        # To make life easier we convert numpy stuff directly into int. Makes it easier to integrate it with forms and procedure args
        if self._target_class in (np.uint8, np.uint16, np.uint32):
            return int(text)
        
        return self._target_class(text)

class BinaryConverter(Converter):
    ALT_CHARS = b"-_"

    def validate_val(self, value: Any) -> bool:
        return isinstance(value, bytes)

    def convert_val_to_str(self, value: Any) -> str:
        assert (self.validate_val(value))
        return str(b64encode(value, self.ALT_CHARS))

    def validate_str(self, text: str) -> bool: 
        try:
            b64decode(text, self.ALT_CHARS, validate=True)
        except Exception:
            return False
        else:
            return True

    def convert_str_to_val(self, text: str) -> Any: 
        assert(self.validate_str(text))
        return b64decode(text, self.ALT_CHARS)



def get_converter(target_class: Any) -> Converter:
    if issubclass(target_class, Enum):
        return EnumConverter(target_class)
    elif issubclass(target_class, Version):
        return VersionConverter()    
    elif issubclass(target_class, Timestamp):
        return TimestampConverter() 
    elif issubclass(target_class, bytes):
        return BinaryConverter() 
    else:
        return PrimitiveTypeConverter(target_class)

