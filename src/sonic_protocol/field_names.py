
from enum import unique, auto
from sonic_protocol.schema import IEFieldName

@unique
class BaseFieldName(IEFieldName):
    UNDEFINED = 0
    COMMAND_CODE = 1
    
    ERROR_MESSAGE = 2
    MESSAGE = 3


@unique
class EFieldName(IEFieldName):
    UNDEFINED = BaseFieldName.UNDEFINED.value
    COMMAND_CODE = BaseFieldName.COMMAND_CODE.value
    
    ERROR_MESSAGE = BaseFieldName.ERROR_MESSAGE.value
    MESSAGE = BaseFieldName.MESSAGE.value

    SUCCESS = auto()
    UNKNOWN_ANSWER = auto()

    HELP = auto()

    DEVICE_TYPE = auto()
    PROTOCOL_VERSION = auto()
    IS_RELEASE = auto()
    ADDITIONAL_OPTIONS = auto()

    INDEX = auto()

    TRANSDUCER_ID = auto()
    FREQUENCY = auto()
    SWF = auto()
    GAIN = auto()
    TEMPERATURE = auto()
    SIGNAL = auto()
    WAVEFORM = auto()
    URMS = auto()
    IRMS = auto()
    PHASE = auto()
    TS_FLAG = auto()
    PROCEDURE = auto()
    PROCEDURE_ARG = auto()
    ERROR_CODE = auto()
    DEVICE_STATE = auto() # only used internally

    TIMING = auto()

    ATF = auto()
    ATK = auto()
    ATT = auto()
    ATON = auto()

    BUILD_DATE = auto()
    BUILD_HASH = auto()
    HARDWARE_VERSION = auto()
    FIRMWARE_VERSION = auto()

    INPUT_SOURCE = auto()
    COMM_MODE = auto()
    COMMUNICATION_CHANNEL = auto()
    COMMUNICATION_PROTOCOL = auto()
    TERMINATION = auto()

    TIMESTAMP = auto()

    SCAN_F_CENTER = auto()
    SCAN_F_RANGE = auto()
    SCAN_F_STEP = auto()
    SCAN_F_SHIFT = auto()
    SCAN_T_STEP = auto()
    SCAN_GAIN = auto()
    TUNE_F_STEP = auto()
    TUNE_F_SHIFT = auto()
    TUNE_T_TIME = auto()
    TUNE_T_STEP = auto()
    TUNE_N_STEPS = auto()
    TUNE_GAIN = auto()
    WIPE_F_RANGE = auto()
    WIPE_F_STEP = auto()
    WIPE_T_ON = auto()
    WIPE_T_OFF = auto()
    WIPE_T_PAUSE = auto()
    RAMP_F_START = auto()
    RAMP_F_STOP = auto()
    RAMP_F_STEP = auto()
    RAMP_T_ON = auto()
    RAMP_T_OFF = auto()
    DUTY_CYCLE_T_OFF = auto()
    DUTY_CYCLE_T_ON = auto()

    LOG_LEVEL = auto()
    LOGGER_NAME = auto()

    # Legacy Fields
    LEGACY_RANG = auto()
    LEGACY_STEP = auto()
    LEGACY_SING = auto()
    LEGACY_PAUS = auto()
    LEGACY_TUST = auto()
    LEGACY_TUTM = auto()
    LEGACY_SCST = auto()
    LEGACY_F_CENTER = auto()
    LEGACY_POLL = auto()


