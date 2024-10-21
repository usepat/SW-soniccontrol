from enum import Enum, IntEnum, auto
from typing import Any, Dict, List, Tuple, TypeVar, Generic
import attrs

VersionTuple = Tuple[int, int, int]

@attrs.define(order=True) # order True, lets attrs define automatically comparision methods
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

class CommandCode(IntEnum):
    """!
    Command codes are the bridge between the commands implemented in python and c++ and the 
    CommandDefs in the generated CommandLookups from the protocol_builder.

    They are used as a unique identifier and to seperate the protocol and definition logic,
    from the actual command and answer implementation.
    """
    # legacy commands, that are not supported anymore have negative numbers
    GET_TYPE = -1

    INVALID = 0
    UNIMPLEMENTED = 1
    SHUT_DOWN = 2
    LIST_AVAILABLE_COMMANDS = 3
    GET_HELP = 4
    # NOTIFY = 5 (commented out in the original)
    GET_PROTOCOL = 6
    EQUALSIGN = 10
    DASH = 20

    QUESTIONMARK = 30
    GET_INFO = 40
    GET_FREQ = 50
    GET_GAIN = 60
    GET_TEMP = 70
    GET_TMCU = 80
    GET_UIPT = 90
    GET_ADC = 100
    GET_PROT = 110
    GET_PROT_LIST = 120
    GET_PVAL = 130
    GET_ATF = 140
    GET_TON = 150
    GET_ATK = 160
    GET_ATT = 171
    GET_SWF = 180
    GET_AUTO = 210
    GET_SCAN = 300
    GET_TUNE = 310
    GET_WIPE = 320

    SET_INPUT_SOURCE = 1010
    SET_ANALOG = 1020
    SET_DAC0 = 1031
    SET_DAC1 = 1032
    SET_KHZ = 1040
    SET_FREQ = 1050
    SET_GAIN = 1060
    SET_MHZ = 1070
    SET_ON = 1080
    SET_OFF = 1090
    SET_WIPE = 1100
    SET_PROC = 1110
    SET_WIPE_X = 1120
    SET_RAMP = 1130
    SET_ATF = 1140
    SET_TON = 1150
    SET_TOFF = 1151
    SET_ATK = 1160
    SET_AUTO = 1210
    SET_RAMPD = 1220
    SET_SWF = 1260
    SET_TERMINATION = 1270
    SET_COM_PROT = 1280
    SET_PHYS_COM_CHANNEL = 1290 
    SET_SCAN = 1300
    SET_TUNE = 1310
    SET_GEXT = 1320
    SET_ATT = 1330
    SET_ATON = 1340

    SET_MANUAL = 5000
    SET_DEFAULT = 6000
    SET_FLASH_USB = 7001
    SET_FLASH_9600 = 7002
    SET_FLASH_115200 = 7003
    SET_NOTIFY = 999
    SET_DUTY_CYCLE = 8000
    SET_LOG_DEBUG = 9000
    SET_LOG_INFO = 10000
    SET_LOG_WARN = 11000
    SET_LOG_ERROR = 12000
    SET_SCAN_F_RANGE = 13000 
    SET_SCAN_F_STEP = 13001
    SET_SCAN_T_STEP = 13002
    SET_TUNE_F_STEP = 13003
    SET_TUNE_T_TIME = 13004
    SET_TUNE_T_STEP = 13005
    SET_WIPE_F_RANGE = 13006
    SET_WIPE_F_STEP = 13007
    SET_WIPE_T_ON = 13008
    SET_WIPE_T_OFF = 13009
    SET_WIPE_T_PAUSE = 13010
    SET_RAMP_F_START = 13011
    SET_RAMP_F_STOP = 13012
    SET_RAMP_F_STEP = 13013
    SET_RAMP_T_ON = 13014
    SET_RAMP_T_OFF = 13015

    E_INTERNAL_DEVICE_ERROR = 20000
    E_COMMAND_NOT_KNOWN = 20001
    E_COMMAND_NOT_IMPLEMENTED = 20002
    E_COMMAND_NOT_PERMITTED = 20003
    E_SYNTAX_ERROR = 20004
    E_INVALID_VALUE = 20005
    E_PARSING_ERROR = 20006

class SIUnit(Enum):
    METER = "m"
    SECONDS = "s"
    HERTZ = "Hz"
    CELSIUS = "C°"
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

class InputSource(Enum):
    MANUAL = "manual" #! control by the user pressing buttons on the device
    EXTERNAL_COMMUNICATION = "external" #! control by sending commands over a communication channel
    ANALOG = "analog" #! control over pins and analog signals, that have predefined meanings

class CommunicationChannel(Enum):
    USB = "usb"
    RS485 = "rs485"
    RS232 = "rs232"

class CommunicationProtocol(Enum):
    SONIC = "sonic"
    MODBUS = "modbus"

@attrs.define()
class DeviceParamConstants:
    max_frequency: int = attrs.field(default=10000001)
    min_frequency: int = attrs.field(default=100000)
    max_gain: int = attrs.field(default=150)
    min_gain: int = attrs.field(default=0)
    max_swf: int = attrs.field(default=15)
    min_swf: int = attrs.field(default=0)

class DeviceParamConstantType(Enum):
    MAX_FREQUENCY = "max_frequency"
    MIN_FREQUENCY = "min_frequency"
    MAX_GAIN = "max_gain"
    MIN_GAIN = "min_gain"
    MAX_SWF = "max_swf"
    MIN_SWF = "min_swf"

@attrs.define()
class MetaExportDescriptor:
    """
    The MetaExportDescriptor is used to define the conditions under which the export is valid.
    """
    min_protocol_version: Version = attrs.field(converter=Version.to_version) #! The minimum protocol version that is required for this export  
    deprecated_protocol_version: Version | None = attrs.field(
        converter=attrs.converters.optional(Version.to_version), # this is needed to support none values
        default=None
    ) #! The protocol version after which this export is deprecated, so it is the maximum version
    included_device_types: List[DeviceType] | None = attrs.field(default=None) #! The device types that are included in this export
    excluded_device_types: List[DeviceType] | None = attrs.field(default=None) #! The device types that are excluded from this export

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
@attrs.define()
class MetaExport(Generic[E]):
    """!
    With the MetaExport you can define under which conditions, you want to export the data.
    So you can define that a command is only exported for a specific version or device type.
    """
    exports: E = attrs.field()
    descriptor: MetaExportDescriptor = attrs.field()

@attrs.define()
class SonicTextAnswerFieldAttrs:
    """!
    The SonicTextAnswerAttrs are used to define how the AnswerField is formatted.
    """
    prefix: str = attrs.field(default="") #! The prefix is added at front of the final message
    postfix: str = attrs.field(default="") #! The postfix is added at the end of the final message

@attrs.define()
class SonicTextAnswerAttrs:
    separator: str = attrs.field(default="#") #! The separator is used to separate the answer fields

@attrs.define()
class SonicTextCommandAttrs:
    string_identifier: str | List[str] = attrs.field() #! The string identifier is used to identify the command
    kwargs: Dict[str, Any] = attrs.field(default={}) #! The kwargs are passed to the communicator. Needed for the old legacy communicator

@attrs.define()
class UserManualAttrs:
    description: str | None = attrs.field(default=None)
    example: str | None = attrs.field(default=None)


T = TypeVar("T", int, float, bool, str, Version, Enum)
AttrsExport = E | List[MetaExport[E]]

@attrs.define()
class FieldType(Generic[T]):
    """!
    Defines the type of a field in the protocol. 
    Can be used for an answer field or command parameter.
    """
    field_type: type[T] = attrs.field()
    allowed_values: List[T] | None = attrs.field(default=None)
    max_value: T | None | DeviceParamConstantType = attrs.field(default=None)
    min_value: T | None | DeviceParamConstantType = attrs.field(default=None)
    si_unit: SIUnit | None = attrs.field(default=None)
    si_prefix: SIPrefix | None = attrs.field(default=None)
    converter_ref: ConverterType = attrs.field(default=ConverterType.PRIMITIVE) #! converters are defined in the code and the protocol only references to them


def to_field_type(value: Any) -> FieldType:
    if isinstance(value, FieldType):
        return value
    return FieldType(value)

@attrs.define()
class CommandParamDef(Generic[T]):
    name: str = attrs.field(converter=str)
    param_type: FieldType[T] = attrs.field(converter=to_field_type)
    user_manual_attrs: AttrsExport[UserManualAttrs] = attrs.field(default=UserManualAttrs())

@attrs.define()
class CommandDef():
    """!
    The CommandDef defines a command call in the protocol.
    It can have an index parameter and a setter parameter.
    Additional params are not defined yet. And not foreseen for the future.
    """
    sonic_text_attrs: AttrsExport[SonicTextCommandAttrs] = attrs.field()
    index_param: CommandParamDef | None = attrs.field(default=None)
    setter_param: CommandParamDef | None = attrs.field(default=None)
    user_manual_attrs: AttrsExport[UserManualAttrs] = attrs.field(default=UserManualAttrs())

@attrs.define(hash=True)
class DerivedFromParam:
    """!
    DerivedFromParam is used to define that the field name is derived from a command parameter.
    We need this flexibility to support commands like atk and atf, where we cannot deduce else wise for
    which atf 0-4 we are talking about.
    """
    param: str = attrs.field()

FieldName = Any | DerivedFromParam
FieldPath = Tuple[FieldName, ...]

def to_field_path(value: Any) -> FieldPath:
    if isinstance(value, list):
        return tuple(value)
    if not isinstance(value, tuple):
        return (value, )
    return value

@attrs.define()
class AnswerFieldDef(Generic[T]):
    """!
    The AnswerFieldDef defines a field in the answer of a command.
    """
    field_path: FieldPath = attrs.field(converter=to_field_path) #! The field path is used to define the attribute name. It is a path to support nested attributes
    field_type: FieldType[T] = attrs.field(converter=to_field_type)
    user_manual_attrs: AttrsExport[UserManualAttrs] = attrs.field(default=UserManualAttrs())
    sonic_text_attrs: AttrsExport[SonicTextAnswerFieldAttrs] = attrs.field(default=SonicTextAnswerFieldAttrs())


@attrs.define()
class AnswerDef():
    """!
    The AnswerDef defines the answer of a command.
    It consists of a list of answer fields.
    """
    fields: List[AnswerFieldDef] = attrs.field()
    user_manual_attrs: AttrsExport[UserManualAttrs] = attrs.field(default=UserManualAttrs())
    sonic_text_attrs: AttrsExport[SonicTextAnswerAttrs] = attrs.field(default=SonicTextAnswerAttrs())


@attrs.define()
class CommandContract:
    """!
    The CommandContract defines a command and the corresponding answer in the protocol.
    It is a contract on how to communicate with each other.
    """
    code: CommandCode = attrs.field()
    command_defs: CommandDef | List[MetaExport[CommandDef]] = attrs.field()
    answer_defs: AnswerDef | List[MetaExport[AnswerDef]] = attrs.field()
    is_release: bool = attrs.field(default=False) #! some commands are only for debugging. They should not be included in release
    tags: List[str] = attrs.field(default=[]) #! tags are used to group commands and to filter them
    user_manual_attrs: AttrsExport[UserManualAttrs] = attrs.field(default=UserManualAttrs())

CommandExport = MetaExport[CommandContract]
CommandListExport = MetaExport[List[CommandContract]]

@attrs.define()
class Protocol:
    """!
    The Protocol defines the protocol of the sonic device.
    It defines on how to communicate with the device.
    It consists of a command lists and the single commands are "exported".
    That means that there are multiple command definitions for a single command and it is specified,
    for which version and device type the command is valid.
    """
    version: Version = attrs.field()
    consts: DeviceParamConstants | List[MetaExport[DeviceParamConstants]] = attrs.field()
    commands: List[CommandExport | CommandListExport] = attrs.field()

