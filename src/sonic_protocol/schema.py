from enum import Enum, IntEnum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Generic, Union
import attrs
import numpy as np

import re
from functools import total_ordering
from datetime import datetime, timezone

from sonic_protocol.groups import GROUPS, GroupId


VersionTuple = Tuple[int, int, int]

@attrs.define(auto_attribs=True, order=True) # order True, lets attrs define automatically comparision methods
class Version:
    major: int = attrs.field()
    minor: int = attrs.field()
    patch: int = attrs.field()

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
        elif isinstance(x, (tuple, list)):
            return Version(*x)
        else:
            raise TypeError("The type cannot be converted into a version")
        

@attrs.define(hash=True, eq=True)
class NumStrValue:
    """
        Because we use modbus and a text based protocol, we
        need for enum values a string and number presentation,
        that needs to be hardcoded (no use of auto(), because then it depends on ordering)
    """
    num_val: int
    str_val: str

    def __str__(self) -> str:
            return self.str_val
    
    def __int__(self) -> int:
        return self.num_val

    def __index__(self) -> int:
        return self.num_val

class NumStrEnum(Enum):
    @classmethod
    def _missing_(cls, value):
        for member in cls:
            if isinstance(value, str) and value == member.value.str_val:
                return member
            if isinstance(value, int) and value == member.value.num_val:
                return member
        return None
        
class IEFieldName(IntEnum):
    ...

class ICommandCode(IntEnum):
    ...

class BuildType(NumStrEnum):
    DEBUG = NumStrValue(0, "DEBUG")
    RELEASE = NumStrValue(1, "RELEASE")

class DeviceType(NumStrEnum):
    DESCALE = NumStrValue(0, "descale")
    MVP_WORKER = NumStrValue(1, "mvp_worker")
    POSTMAN = NumStrValue(2, "postman")
    CRYSTAL = NumStrValue(3, "crystal")
    UNKNOWN = NumStrValue(4, "unknown")
    CONFIGURATOR = NumStrValue(5, "configurator")
    SIMULATION = NumStrValue(6, "simulation")
    DIAGNOSTICS_TOOL = NumStrValue(7, "diagnostics_tool")

class TransducerState(NumStrEnum):
    IDLE = NumStrValue(0, "idle")
    BUSY = NumStrValue(1, "busy")
    TRANSDUCER_NOT_CONNECTED = NumStrValue(2, "not connected")
    TRANSDUCER_TOO_HOT = NumStrValue(3, "too hot")
    TRANSDUCER_SHORTED = NumStrValue(4, "shorted")
    TRANSDUCER_NOT_SUBMERGED = NumStrValue(5, "not submerged")
    TRANSDUCER_CHARACTERISTICS_CHANGED = NumStrValue(6, "characteristics changed")

class SystemState(NumStrEnum):
    OK = NumStrValue(0, "ok")
    RECOVERED = NumStrValue(1, "recovered")
    NO_COMM = NumStrValue(2, "no comm")
    COMPONENT_DAMAGED = NumStrValue(3, "damaged")


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

    # This is so ugly. We need a better way to transport times
    MINUTE = "minutes"

@total_ordering
class SIPrefix(Enum):
    NANO  = 'n'
    MICRO = 'u'
    MILLI = 'm'
    DECI  = 'd'
    CENTI = 'c'
    NONE  = ''
    DEKA  = 'da'
    HECTO = 'h'
    KILO  = 'k'
    MEGA  = 'M'
    GIGA  = 'G'

    def __init__(self, symbol: str) -> None:
        self.symbol = symbol

    def _map_symbol_to_factor(self) -> int:
        # Map each symbol to its exponent
        match self.symbol:
            case 'n':  # NANO
                return -9
            case 'u':  # MICRO
                return -6
            case 'm':  # MILLI
                return -3
            case 'd':  # DECI
                return -2
            case 'c':  # CENTI
                return -1
            case '':   # NONE
                return 0
            case 'da': # DEKA
                return 1
            case 'h':  # HECTO
                return 2
            case 'k':  # KILO
                return 3
            case 'M':  # MEGA
                return 6
            case 'G':  # GIGA
                return 9
            case _:
                raise ValueError(f"Unknown SI prefix symbol: {self.symbol}")

    @property
    def exponent(self):
        return self._map_symbol_to_factor()

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

    def __hash__(self):
        return hash(self.exponent)


class InputSource(NumStrEnum):
    EXTERNAL = NumStrValue(0, "external") #! control by sending commands over a communication channel
    ANALOG = NumStrValue(1, "analog") #! control over pins and analog signals, that have predefined meanings
    RELAY = NumStrValue(2, "relay") #! control over pins and digital signals, that have predefined meanings
    DIGITAL = NumStrValue(3, "digital") #! control over pins and digital signals, that have predefined meanings
    # MANUAL = EnumMemValue(4, "manual") #! control by the user pressing buttons on the device
    # Manual command should not be allowed to be send over serial


class ControlMode(NumStrEnum):
    REMOTE = NumStrValue(0, "remote")
    ANALOG = NumStrValue(1, "analog")
    DIGITAL = NumStrValue(2, "digital")
    AUTO = NumStrValue(3, "auto")

class CommunicationChannel(NumStrEnum):
    USB = NumStrValue(0, "usb")
    RS485 = NumStrValue(1, "rs485")
    RS232 = NumStrValue(2, "rs232")

class CommunicationProtocol(NumStrEnum):
    SONIC = NumStrValue(0, "sonic")
    MODBUS = NumStrValue(1, "modbus")

class Procedure(NumStrEnum):
    NO_PROC = NumStrValue(0, "none")
    AUTO = NumStrValue(1, "auto")
    TUNE = NumStrValue(2, "tune")
    SCAN = NumStrValue(3, "scan")
    WIPE = NumStrValue(4, "wipe")
    RAMP = NumStrValue(5, "ramp")
    DUTY_CYCLE = NumStrValue(6, "duty_cycle")
    ANOMALY_ROUTINE = NumStrValue(7, "anomaly_routine")

class Anomaly(NumStrEnum):
    SUBMERGED = NumStrValue(0, "submerged")
    AIR = NumStrValue(1, "air")
    BUBBLES = NumStrValue(2, "bubbles")


class Waveform(NumStrEnum):
    SINE = NumStrValue(0, "sine")
    SQUARE = NumStrValue(1, "square")

class Loglevel(NumStrEnum):
    DEBUG = NumStrValue(0, "DEBUG")
    INFO = NumStrValue(1, "INFO")
    WARN = NumStrValue(2, "WARN")
    ERROR = NumStrValue(3, "ERROR")
    DISABLED = NumStrValue(4, "DISABLED")
    DEBUG_EXTENSIVE = NumStrValue(5, "DEBUG_EXTENSIVE")

# TODO: upgrade to python 3.13 so we can use the deprecated decorator
# @deprecated("Got replaced in protocol v3.0.0 by a simple string")
class LoggerName(NumStrEnum):
    APP_LOGGER = NumStrValue(0, "appLogger")
    TRANSDUCER_LOGGER = NumStrValue(1, "transducerLogger")
    HWFC_LOGGER = NumStrValue(2, "hwfcLogger")
    PROCEDURE_LOGGER = NumStrValue(3, "procedureLogger")
    GLOBAL = NumStrValue(4, "global")

class Signal(NumStrEnum):
    ON = NumStrValue(0, "ON")
    OFF = NumStrValue(1, "OFF")

class Activation(NumStrEnum):
    ACTIVATED = NumStrValue(0, "activated")
    DEACTIVATED = NumStrValue(1, "deactivated")


@attrs.define()
class Timestamp():
    hour: int = attrs.field()
    minute: int = attrs.field()
    second: int = attrs.field()
    day: int = attrs.field()
    month: int = attrs.field()
    year: int = attrs.field()
    def __str__(self) -> str:
        return f"{self.hour}:{self.minute}:{self.second}-{self.day}.{self.month}.{self.year}"
    
    @staticmethod
    def now() -> "Timestamp":
        now = datetime.now()
        return Timestamp.to_timestamp(now)

    def to_datetime(self)-> datetime:
        return datetime(self.year, self.month, self.day, self.hour, self.minute, self.second, tzinfo=timezone.utc)

    @staticmethod
    def to_timestamp(x: Any) -> "Timestamp":
        if isinstance(x, Timestamp):
            return x
        if isinstance(x, datetime):
            return Timestamp(
                hour=x.hour,
                minute=x.minute,
                second=x.second,
                day=x.day,
                month=x.month,
                year=x.year
            )
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

    # TODO maybe fix these defaults somewhere more explicitly because if they get changed randomly it might cause
    ## backwards compatibility issues
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

    def get_constant_value_from_type(self, type: "DeviceParamConstantType"):
        return getattr(self, type.value)




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
    @staticmethod
    def str_identifier_convert_func(x: Any):
        if isinstance(x, str):
            return [x]
        elif isinstance(x, list):
            return x
        else:
            raise TypeError("Value cannot be converted into a list of str")


    string_identifier: List[str] = attrs.field(converter=str_identifier_convert_func) #! The string identifier is used to identify the command
    kwargs: Dict[str, Any] = attrs.field(default={}) #! The kwargs are passed to the communicator. Needed for the old legacy communicator

@attrs.define(auto_attribs=True)
class UserManualAttrs:
    description: Optional[str] = attrs.field(default=None)
    example: Optional[str] = attrs.field(default=None)

T = TypeVar("T", int, np.uint8, np.uint16, np.uint32, float, bool, str, 
            bytes, Version, Enum, Timestamp, )

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

def to_field_type(value: Any) -> FieldType:
    if isinstance(value, FieldType):
        return value
    return FieldType(value)

"""
    CommandParamDef and AnswerFieldDef should be merged in the future.
    However to refactor that is quite a lot of work. 
    Therefore this class is used instead to provide a better interface.
"""
@attrs.define(auto_attribs=True)
class FieldDef:
    name: IEFieldName = attrs.field()
    field_type: FieldType = attrs.field(converter=to_field_type)
    user_manual_attrs: UserManualAttrs = attrs.field(default=UserManualAttrs())

@attrs.define(auto_attribs=True)
class CommandParamDef():
    name: IEFieldName = attrs.field()
    param_type: FieldType = attrs.field(converter=to_field_type)
    user_manual_attrs: UserManualAttrs = attrs.field(default=UserManualAttrs())
    def __hash__(self):
        return hash((self.name, self.param_type.field_type, self.param_type.si_unit, self.param_type.si_prefix, self.param_type.max_value, self.param_type.min_value))

    def to_field_def(self) -> FieldDef:
        return FieldDef(name=self.name, field_type=self.param_type, user_manual_attrs=self.user_manual_attrs)
        

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

    def field_defs(self) -> List[FieldDef]:
        result: List[FieldDef] = []

        if self.index_param:
            result.append(self.index_param.to_field_def())
        if self.setter_param:
            result.append(self.setter_param.to_field_def())

        return result

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
        return hash((self.field_name, self.field_type.field_type, self.field_type.si_unit, self.field_type.si_prefix, self.field_type.max_value, self.field_type.min_value))

    def to_field_def(self) -> FieldDef:
        return FieldDef(name=self.field_name, field_type=self.field_type, user_manual_attrs=self.user_manual_attrs)

@attrs.define(auto_attribs=True)
class AnswerDef():
    """!
    The AnswerDef defines the answer of a command.
    It consists of a list of answer fields.
    """
    fields: List[AnswerFieldDef] = attrs.field()
    user_manual_attrs: UserManualAttrs = attrs.field(default=UserManualAttrs())
    sonic_text_attrs: SonicTextAnswerAttrs = attrs.field(default=SonicTextAnswerAttrs())

    def field_defs(self) -> List[FieldDef]:
        return [ answer_field.to_field_def() for answer_field in self.fields ]

    def replace_field_def(self, field: AnswerFieldDef):
        for i in range(len(self.fields)):
            if self.fields[i].field_name == field.field_name:
                self.fields[i] = field
                
    
    def add_field(self, field: AnswerFieldDef):
        self.fields.append(field)
            


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
    is_admin_command: bool = attrs.field(default=False)
    tags: List[str] = attrs.field(default=[]) #! tags are used to group commands and to filter them
    group_id: GroupId = attrs.field(default=GROUPS.misc)
    user_manual_attrs: UserManualAttrs = attrs.field(default=UserManualAttrs())

    def replace_string_identifier(self, mappings: dict[str, str]):
        if self.command_def is None:
            return
        if self.command_def.sonic_text_attrs is None:
            return
        string_identifier = self.command_def.sonic_text_attrs.string_identifier
        for i, s in enumerate(string_identifier):
            if s in mappings:
                string_identifier[i] = mappings[s]
        self.command_def.sonic_text_attrs.string_identifier = string_identifier


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
    command_code_for_validation_converter: Callable[[int], int] = attrs.field()
    consts: DeviceParamConstants = attrs.field(factory=DeviceParamConstants)

    def convert_command_code_for_validation(self, code: int) -> int:
        return self.command_code_for_validation_converter(code)

