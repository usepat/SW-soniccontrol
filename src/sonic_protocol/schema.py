from enum import Enum, IntEnum, auto
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Generic, Union
import attrs
import numpy as np

import re
from functools import total_ordering


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
        
        
class IEFieldName(IntEnum):
    ...

class ICommandCode(IntEnum):
    ...

class BuildType(Enum):
    DEBUG = "DEBUG"
    RELEASE = "RELEASE"

class DeviceType(Enum):
    UNKNOWN = "unknown"
    DESCALE = "descale"
    MVP_WORKER = "mvp_worker"
    CRYSTAL = "crystal"
    CONFIGURATOR = "configurator"

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

@total_ordering
class SIPrefix(Enum):
    NANO  = ('n', -9)
    MICRO = ('u', -6)
    MILLI = ('m', -3)
    DECI  = ('d', -2)
    CENTI = ('c', -1)
    NONE  = ('' , 0) #(base unit, no prefix)
    KILO  = ('k', 3)
    MEGA  = ('M', 6)
    GIGA  = ('G', 9)

    def __init__(self, symbol: str, exponent: int) -> None:
        self.symbol = symbol
        self.exponent = exponent

    @property
    def factor(self):
        return 1 if self.exponent == 0 else 10 ** self.exponent
    
    def __eq__(self, other):
        if isinstance(other, SIPrefix):
            return self.exponent == other.exponent
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, SIPrefix):
            return self.exponent < other.exponent
        return NotImplemented

class ConverterType(Enum):
    """!
    Converters are used to convert the data send to the right class.
    We only reference them in the protocol, instead of supplying the converters,
    because the converters need to be implemented once in the firmware and once in the remote_controller code.
    """
    VERSION = auto()
    ENUM = auto()
    PRIMITIVE = auto()
    TIMESTAMP = auto()

class InputSource(Enum):
    EXTERNAL = "external" #! control by sending commands over a communication channel
    ANALOG = "analog" #! control over pins and analog signals, that have predefined meanings
    RELAY = "relay" #! control over pins and digital signals, that have predefined meanings
    DIGITAL = "digital" #! control over pins and digital signals, that have predefined meanings
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
    DUTY_CYCLE = "duty_cycle"

class Anomaly(Enum):
    submerged = "submerged"
    AIR = "air"
    BUBBLES = "bubbles"


class Waveform(Enum):
    SINE = "sine"
    SQUARE = "square"

class Loglevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    DISABLED = "DISABLED"
    DEBUG_EXTENSIVE = "DEBUG_EXTENSIVE"

class LoggerName(Enum):
    APP_LOGGER = "appLogger"
    TRANSDUCER_LOGGER = "transducerLogger"
    HWFC_LOGGER = "hwfcLogger"
    PROCEDURE_LOGGER = "procedureLogger"
    GLOBAL = "global"

class Signal(Enum):
    ON = "ON"
    OFF = "OFF"

class Activation(Enum):
    ACTIVATED = "activated"
    DEACTIVATED = "deactivated"


@attrs.define()
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
    max_transducer_index: int = attrs.field(default=4)
    min_transducer_index: int = attrs.field(default=1)

    max_frequency: int = attrs.field(default=10000000)
    min_frequency: int = attrs.field(default=100000)
    max_gain: int = attrs.field(default=150)
    min_gain: int = attrs.field(default=0)
    max_swf: int = attrs.field(default=15)
    min_swf: int = attrs.field(default=0)

    max_f_step: int = attrs.field(default=5000000)
    min_f_step: int = attrs.field(default=1)
    max_f_shift: int = attrs.field(default=10000)
    min_f_shift: int = attrs.field(default=0)

    max_t_on: int = attrs.field(default=1000 * 60 * 60) # in milliseconds
    min_t_on: int = attrs.field(default=10)
    max_t_off: int = attrs.field(default=1000 * 60 * 60)
    min_t_off: int = attrs.field(default=0)

    max_duty_cycle_t_on: int = attrs.field(default=300 * 60) # in seconds
    min_duty_cycle_t_on: int = attrs.field(default=1 * 60)
    max_duty_cycle_t_off: int = attrs.field(default=300 * 60)
    min_duty_cycle_t_off: int = attrs.field(default=0)

    min_n_steps: int = attrs.field(default=1)


class DeviceParamConstantType(Enum):
    MAX_TRANSDUCER_INDEX = "max_transducer_index"
    MIN_TRANSDUCER_INDEX = "min_transducer_index"
    MAX_FREQUENCY = "max_frequency"
    MIN_FREQUENCY = "min_frequency"
    MAX_GAIN = "max_gain"
    MIN_GAIN = "min_gain"
    MAX_SWF = "max_swf"
    MIN_SWF = "min_swf"
    MAX_F_STEP = "max_f_step"
    MIN_F_STEP = "min_f_step"
    MAX_F_SHIFT = "max_f_shift"
    MIN_F_SHIFT = "min_f_shift"
    MAX_T_ON = "max_t_on"
    MIN_T_ON = "min_t_on"
    MAX_T_OFF = "max_t_off"
    MIN_T_OFF = "min_t_off"
    MAX_DUTY_CYCLE_T_ON = "max_duty_cycle_t_on"
    MIN_DUTY_CYCLE_T_ON = "min_duty_cycle_t_on"
    MAX_DUTY_CYCLE_T_OFF = "max_duty_cycle_t_off"
    MIN_DUTY_CYCLE_T_OFF = "min_duty_cycle_t_off"
    MIN_N_STEPS = "min_n_steps"


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

T = TypeVar("T", int, np.uint8, np.uint16, np.uint32, float, bool, str, Version, Enum, Timestamp)

@attrs.define(auto_attribs=True)
class FieldType(Generic[T]):
    """!
    Defines the type of a field in the protocol. 
    Can be used for an answer field or command parameter.
    """
    field_type: type[T] = attrs.field()
    allowed_values: Optional[Tuple[T, ...]] = attrs.field(default=None)
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
    name: IEFieldName = attrs.field()
    param_type: FieldType = attrs.field(converter=to_field_type)
    user_manual_attrs: UserManualAttrs = attrs.field(default=UserManualAttrs())
    def __hash__(self):
        return hash((self.name, self.param_type.field_type, self.param_type.converter_ref, self.param_type.si_unit, self.param_type.si_prefix, self.param_type.max_value, self.param_type.min_value))


@attrs.define(auto_attribs=True)
class CommandDef():
    """!
    The CommandDef defines a command call in the protocol.
    It can have an index parameter and a setter parameter.
    Additional params are not defined yet. And not foreseen for the future.
    """
    sonic_text_attrs: SonicTextCommandAttrs = attrs.field()
    index_param: Optional[CommandParamDef] = attrs.field(default=None)
    setter_param: Optional[CommandParamDef] = attrs.field(default=None)
    user_manual_attrs: UserManualAttrs = attrs.field(default=UserManualAttrs())


@attrs.define(auto_attribs=True)
class AnswerFieldDef():
    """!
    The AnswerFieldDef defines a field in the answer of a command.
    """
    field_name: IEFieldName = attrs.field() #! The field path is used to define the attribute name. It is a path to support nested attributes
    field_type: FieldType = attrs.field(converter=to_field_type)
    user_manual_attrs: UserManualAttrs = attrs.field(default=UserManualAttrs())
    sonic_text_attrs: SonicTextAnswerFieldAttrs = attrs.field(default=SonicTextAnswerFieldAttrs())

    def __hash__(self):
        return hash((self.field_name, self.field_type.field_type, self.field_type.converter_ref, self.field_type.si_unit, self.field_type.si_prefix, self.field_type.max_value, self.field_type.min_value))



@attrs.define(auto_attribs=True)
class AnswerDef():
    """!
    The AnswerDef defines the answer of a command.
    It consists of a list of answer fields.
    """
    fields: List[AnswerFieldDef] = attrs.field()
    user_manual_attrs: UserManualAttrs = attrs.field(default=UserManualAttrs())
    sonic_text_attrs: SonicTextAnswerAttrs = attrs.field(default=SonicTextAnswerAttrs())


@attrs.define(auto_attribs=True)
class CommandContract:
    """!
    The CommandContract defines a command and the corresponding answer in the protocol.
    It is a contract on how to communicate with each other.
    """
    code: ICommandCode = attrs.field()
    command_def: Union[None, CommandDef] = attrs.field()
    answer_def: AnswerDef = attrs.field()
    is_release: bool = attrs.field(default=False) #! some commands are only for debugging. They should not be included in release
    tags: List[str] = attrs.field(default=[]) #! tags are used to group commands and to filter them
    user_manual_attrs: UserManualAttrs = attrs.field(default=UserManualAttrs())


@attrs.define(auto_attribs=True)
class ProtocolType:
    version: Version = attrs.field()
    device_type: DeviceType = attrs.field()
    is_release: bool = False
    additional_opts: str | None = None

@attrs.define(auto_attribs=True)
class Protocol:
    """!
    The Protocol defines the protocol of the sonic device.
    It defines on how to communicate with the device.
    It consists of a command lists and the single commands are "exported".
    That means that there are multiple command definitions for a single command and it is specified,
    for which version and device type the command is valid.
    """
    info: ProtocolType = attrs.field()
    custom_data_types: Dict[str, type] = attrs.field()
    command_code_cls: type[ICommandCode] = attrs.field()
    field_name_cls: type[IEFieldName] = attrs.field()
    command_contracts: Dict[ICommandCode, CommandContract] = attrs.field()
    consts: DeviceParamConstants= attrs.field(default=DeviceParamConstants())
    
