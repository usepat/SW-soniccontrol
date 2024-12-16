from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Generic, Union
import attrs
import numpy as np

from sonic_protocol.command_codes import CommandCode
from sonic_protocol.field_names import EFieldName
import re

VersionTuple = Tuple[int, int, int]

@attrs.define(auto_attribs=True, order=True) # order True, lets attrs define automatically comparision methods
class Version:
    major: int = attrs.field()
    minor: int = attrs.field()
    patch: int = attrs.field()
    # TODO: make that the version can be converted to a list and created from a list by default

    def __iter__(self):
        return iter((self.major, self.minor, self.patch))
    
    def __str__(self) -> str:
        return f"v{self.major}.{self.minor}.{self.patch}"
    
    @staticmethod
    def to_version(x: Any) -> "Version":
        if isinstance(x, Version):
            return x
        if isinstance(x, str):
            if x[0] == "v":
                x = x[1:]
            version = tuple(map(int, x.split(".")))
            if len(version) != 3:
                raise ValueError("The Version needs to have exactly two separators '.'")
            return Version(*version)
        elif isinstance(x, tuple):
            return Version(*x)
        else:
            raise TypeError("The type cannot be converted into a version")


class DeviceType(Enum):
    UNKNOWN = "unknown"
    DESCALE = "descale"
    CATCH = "catch"
    WIPE = "wipe"
    MVP_WORKER = "mvp_worker"

class SIUnit(Enum):
    METER = "m"
    SECONDS = "s"
    HERTZ = "Hz"
    CELSIUS = "C°"
    KELVIN = "K"
    VOLTAGE = "V"
    AMPERE = "A"
    DEGREE = "°"
    PERCENT = "%"

class SIPrefix(Enum):
    NANO  = 'n'   # 10⁻⁹
    MICRO = 'u'   # 10⁻⁶
    MILLI = 'm'   # 10⁻³
    NONE  = ''    # 10⁰ (base unit, no prefix)
    KILO  = 'k'   # 10³
    MEGA  = 'M'   # 10⁶
    GIGA  = 'G'   # 10⁹

class ConverterType(Enum):
    """!
    Converters are used to convert the data send to the right class.
    We only reference them in the protocol, instead of supplying the converters,
    because the converters need to be implemented once in the firmware and once in the remote_controller code.
    """
    SIGNAL = auto()
    VERSION = auto()
    ENUM = auto()
    BUILD_TYPE = auto()
    PRIMITIVE = auto()
    TERMINATION = auto()
    TIMESTAMP = auto()

class InputSource(Enum):
    EXTERNAL_COMMUNICATION = "external" #! control by sending commands over a communication channel
    ANALOG = "analog" #! control over pins and analog signals, that have predefined meanings
    # MANUAL = "manual" #! control by the user pressing buttons on the device
    # Manual command should not be allowed to be send over serial

class CommunicationChannel(Enum):
    USB = "usb"
    RS485 = "rs485"
    RS232 = "rs232"

class CommunicationProtocol(Enum):
    SONIC = "sonic"
    MODBUS = "modbus"

class Procedure(Enum):
    NO_PROC = "none"
    AUTO = "auto"
    TUNE = "tune"
    SCAN = "scan"
    WIPE = "wipe"
    RAMP = "ramp"

class Waveform(Enum):
    SINE = "sine"
    SQUARE = "square"

class Loglevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"

class LoggerName(Enum):
    APP_LOGGER = "app_logger"
    TRANSDUCER_LOGGER = "transducer_logger"
    HWFC_LOGGER = "hwfc_logger"
    PROCEDURE_LOGGER = "procedure_logger"
    GLOBAL = "global"

class Timestamp():
    hour: int = attrs.field()
    minute: int = attrs.field()
    second: int = attrs.field()
    day: int = attrs.field()
    month: int = attrs.field()
    year: int = attrs.field()
    def __str__(self) -> str:
        return f"{self.hour}:{self.minute}:{self.second} {self.day}.{self.month}.{self.year}"
    
    @staticmethod
    def to_timestamp(x: Any) -> "Timestamp":
        if isinstance(x, Timestamp):
            return x
        if isinstance(x, str):
            # Define the regex pattern for the timestamp
            pattern = re.compile(
                r"(\d{1,2})[:._\-](\d{1,2})[:._\-](\d{1,2})[._\- ](\d{1,2})[._\-](\d{1,2})[._\-](\d{4})"
            )

            match = pattern.match(x)
            if match:
                hour, minute, second, day, month, year = map(int, match.groups())
                return Timestamp(hour=hour, minute=minute, second=second, day=day, month=month, year=year)
            else:
                raise ValueError("The string does not match the required timestamp format")
        else:
            raise TypeError("The type cannot be converted into a version")

@attrs.define(auto_attribs=True)
class DeviceParamConstants:
    max_frequency: int = attrs.field(default=10000000)
    min_frequency: int = attrs.field(default=100000)
    max_gain: int = attrs.field(default=150)
    min_gain: int = attrs.field(default=0)
    max_swf: int = attrs.field(default=15)
    min_swf: int = attrs.field(default=0)
    max_transducer_index: int = attrs.field(default=4)
    min_transducer_index: int = attrs.field(default=1)
    max_frequency_step: int = attrs.field(default=5000000)
    min_frequency_step: int = attrs.field(default=100)

class DeviceParamConstantType(Enum):
    MAX_FREQUENCY = "max_frequency"
    MIN_FREQUENCY = "min_frequency"
    MAX_GAIN = "max_gain"
    MIN_GAIN = "min_gain"
    MAX_SWF = "max_swf"
    MIN_SWF = "min_swf"
    MAX_TRANSDUCER_INDEX = "max_transducer_index"
    MIN_TRANSDUCER_INDEX = "min_transducer_index"
    MAX_FREQUENCY_STEP = "max_frequency_step"
    MIN_FREQUENCY_STEP = "min_frequency_step"

@attrs.define(auto_attribs=True)
class MetaExportDescriptor:
    """
    The MetaExportDescriptor is used to define the conditions under which the export is valid.
    """
    min_protocol_version: Version = attrs.field(converter=Version.to_version) #! The minimum protocol version that is required for this export  
    deprecated_protocol_version: Optional[Version] = attrs.field(
        converter=attrs.converters.optional(Version.to_version), # this is needed to support none values
        default=None
    ) #! The protocol version after which this export is deprecated, so it is the maximum version
    included_device_types: Optional[List[DeviceType]] = attrs.field(default=None) #! The device types that are included in this export
    excluded_device_types: Optional[List[DeviceType]] = attrs.field(default=None) #! The device types that are excluded from this export

    def is_valid(self, version: Version, device_type: DeviceType) -> bool:
        if self.min_protocol_version > version:
            return False
        if self.deprecated_protocol_version and self.deprecated_protocol_version <= version:
            return False
        if self.included_device_types and device_type not in self.included_device_types:
            return False
        if self.excluded_device_types and device_type in self.excluded_device_types:
            return False
        return True

E = TypeVar("E")
@attrs.define(auto_attribs=True)
class MetaExport(Generic[E]):
    """!
    With the MetaExport you can define under which conditions, you want to export the data.
    So you can define that a command is only exported for a specific version or device type.
    """
    exports: E = attrs.field()
    descriptor: MetaExportDescriptor = attrs.field()

@attrs.define(auto_attribs=True)
class SonicTextAnswerFieldAttrs:
    """!
    The SonicTextAnswerAttrs are used to define how the AnswerField is formatted.
    """
    prefix: str = attrs.field(default="") #! The prefix is added at front of the final message
    postfix: str = attrs.field(default="") #! The postfix is added at the end of the final message

@attrs.define(auto_attribs=True)
class SonicTextAnswerAttrs:
    separator: str = attrs.field(default="#") #! The separator is used to separate the answer fields

@attrs.define(auto_attribs=True)
class SonicTextCommandAttrs:
    string_identifier: Union[str, List[str]] = attrs.field() #! The string identifier is used to identify the command
    kwargs: Dict[str, Any] = attrs.field(default={}) #! The kwargs are passed to the communicator. Needed for the old legacy communicator

@attrs.define(auto_attribs=True)
class UserManualAttrs:
    description: Optional[str] = attrs.field(default=None)
    example: Optional[str] = attrs.field(default=None)

T = TypeVar("T", int, np.uint8, np.uint16, np.uint32, float, bool, str, Version, Enum)
AttrsExport = Union[E, List[MetaExport[E]]]

@attrs.define(auto_attribs=True)
class FieldType(Generic[T]):
    """!
    Defines the type of a field in the protocol. 
    Can be used for an answer field or command parameter.
    """
    field_type: type[T] = attrs.field()
    allowed_values: Optional[List[T]] = attrs.field(default=None)
    max_value: Union[T, None, DeviceParamConstantType] = attrs.field(default=None)
    min_value: Union[T, None, DeviceParamConstantType] = attrs.field(default=None)
    si_unit: Optional[SIUnit] = attrs.field(default=None)
    si_prefix: Optional[SIPrefix] = attrs.field(default=None)
    converter_ref: ConverterType = attrs.field(default=ConverterType.PRIMITIVE) #! converters are defined in the code and the protocol only references to them

def to_field_type(value: Any) -> FieldType:
    if isinstance(value, FieldType):
        return value
    return FieldType(value)

@attrs.define(auto_attribs=True)
class CommandParamDef():
    name: EFieldName = attrs.field(converter=EFieldName)
    param_type: FieldType = attrs.field(converter=to_field_type)
    user_manual_attrs: AttrsExport[UserManualAttrs] = attrs.field(default=UserManualAttrs())
    def __hash__(self):
        return hash((self.name, self.param_type.field_type, self.param_type.converter_ref, self.param_type.si_unit, self.param_type.si_prefix, self.param_type.max_value, self.param_type.min_value))

    def to_cpp_var_name(self):
        # TODO: move this into cpp trans compiler
        si_unit_name = self.param_type.si_unit.name.lower() if self.param_type.si_unit else "none"
        si_prefix_name = self.param_type.si_prefix.name.lower() if self.param_type.si_prefix else "none"
        if isinstance(self.param_type.min_value, DeviceParamConstantType):
            min_value_name = self.param_type.min_value.name.lower()
        else:
            min_value_name = str(self.param_type.min_value) if self.param_type.min_value else "none"
        if isinstance(self.param_type.max_value, DeviceParamConstantType):
            max_value_name = self.param_type.max_value.name.lower()
        else:
            max_value_name = str(self.param_type.max_value) if self.param_type.max_value else "none"
        var_name = f"{self.name.value.lower()}_{self.param_type.field_type.__name__.lower()}_{si_unit_name}_{si_prefix_name}_{min_value_name}_{max_value_name}"
        var_name = var_name.replace("-", "minus") # fix for negative numbers
        var_name = var_name.replace(".", "_") # fix for floats
        return var_name

@attrs.define(auto_attribs=True)
class CommandDef():
    """!
    The CommandDef defines a command call in the protocol.
    It can have an index parameter and a setter parameter.
    Additional params are not defined yet. And not foreseen for the future.
    """
    sonic_text_attrs: AttrsExport[SonicTextCommandAttrs] = attrs.field()
    index_param: Optional[CommandParamDef] = attrs.field(default=None)
    setter_param: Optional[CommandParamDef] = attrs.field(default=None)
    user_manual_attrs: AttrsExport[UserManualAttrs] = attrs.field(default=UserManualAttrs())


@attrs.define(auto_attribs=True)
class AnswerFieldDef():
    """!
    The AnswerFieldDef defines a field in the answer of a command.
    """
    field_name: EFieldName = attrs.field() #! The field path is used to define the attribute name. It is a path to support nested attributes
    field_type: FieldType = attrs.field(converter=to_field_type)
    user_manual_attrs: AttrsExport[UserManualAttrs] = attrs.field(default=UserManualAttrs())
    sonic_text_attrs: AttrsExport[SonicTextAnswerFieldAttrs] = attrs.field(default=SonicTextAnswerFieldAttrs())
    def __hash__(self):
        return hash((self.field_name, self.field_type.field_type, self.field_type.converter_ref, self.field_type.si_unit, self.field_type.si_prefix, self.field_type.max_value, self.field_type.min_value))
    def to_cpp_var_name(self):
        # TODO: move this function out to transcompiler
        si_unit_name = self.field_type.si_unit.name.lower() if self.field_type.si_unit else "none"
        si_prefix_name = self.field_type.si_prefix.name.lower() if self.field_type.si_prefix else "none"
        if isinstance(self.field_type.min_value, DeviceParamConstantType):
            min_value_name = self.field_type.min_value.name.lower()
        else:
            min_value_name = str(self.field_type.min_value) if self.field_type.min_value else "none"
        if isinstance(self.field_type.max_value, DeviceParamConstantType):
            max_value_name = self.field_type.max_value.name.lower()
        else:
            max_value_name = str(self.field_type.max_value) if self.field_type.max_value else "none"
        if isinstance(self.sonic_text_attrs, SonicTextAnswerFieldAttrs):
            # Remove characters that are not allowed in cpp variable names
            prefix = ''.join(e for e in self.sonic_text_attrs.prefix if e.isalnum())
            postfix = ''.join(e for e in self.sonic_text_attrs.postfix if e.isalnum())
        else:
            prefix = "none"
            postfix = "none"
        var_name = f"{self.field_name.value.lower()}_{self.field_type.field_type.__name__.lower()}_{si_unit_name}_{si_prefix_name}_{min_value_name}_{max_value_name}_{prefix}_{postfix}"
        var_name = var_name.replace("-", "minus") # fix for negative numbers
        var_name = var_name.replace(".", "_") # fix for floats
        return var_name



@attrs.define(auto_attribs=True)
class AnswerDef():
    """!
    The AnswerDef defines the answer of a command.
    It consists of a list of answer fields.
    """
    fields: List[AnswerFieldDef] = attrs.field()
    user_manual_attrs: AttrsExport[UserManualAttrs] = attrs.field(default=UserManualAttrs())
    sonic_text_attrs: AttrsExport[SonicTextAnswerAttrs] = attrs.field(default=SonicTextAnswerAttrs())


@attrs.define(auto_attribs=True)
class CommandContract:
    """!
    The CommandContract defines a command and the corresponding answer in the protocol.
    It is a contract on how to communicate with each other.
    """
    code: CommandCode = attrs.field()
    command_defs: Union[CommandDef, List[MetaExport[CommandDef]]] = attrs.field()
    answer_defs: Union[AnswerDef, List[MetaExport[AnswerDef]]] = attrs.field()
    is_release: bool = attrs.field(default=False) #! some commands are only for debugging. They should not be included in release
    tags: List[str] = attrs.field(default=[]) #! tags are used to group commands and to filter them
    user_manual_attrs: AttrsExport[UserManualAttrs] = attrs.field(default=UserManualAttrs())

CommandExport = MetaExport[CommandContract]
CommandListExport = MetaExport[List[CommandContract]]

@attrs.define(auto_attribs=True)
class Protocol:
    """!
    The Protocol defines the protocol of the sonic device.
    It defines on how to communicate with the device.
    It consists of a command lists and the single commands are "exported".
    That means that there are multiple command definitions for a single command and it is specified,
    for which version and device type the command is valid.
    """
    version: Version = attrs.field()
    commands: List[Union[CommandExport, CommandListExport]] = attrs.field()
    consts: Union[DeviceParamConstants, List[MetaExport[DeviceParamConstants]]] = attrs.field(default=DeviceParamConstants())


