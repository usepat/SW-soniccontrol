from enum import Enum


class EFieldName(Enum):
    UNKNOWN_ANSWER = "unknown_answer"
    SUCCESS = "success"
    
    LIST_COMMANDS = "list_commands"
    HELP = "help"

    FREQUENCY = "freq"
    SWF = "swf"
    GAIN = "gain"
    TEMPERATURE = "temp"
    SIGNAL = "signal"
    URMS = "urms"
    IRMS = "irms"
    PHASE = "phase"
    TS_FLAG = "ts_flag"
    PROCEDURE = "procedure"
    PROCEDURE_ARG = "procedure_arg"
    ERROR_CODE = "error_code"
    ERROR_MESSAGE = "error_message"
    TIMING = "timing"
    MESSAGE = "message"

    ATF = "atf"
    ATK = "atk"
    ATT = "att"
    ATON = "aton"

    DEVICE_TYPE = "device_type"
    PROTOCOL_VERSION = "protocol_version"
    IS_RELEASE = "is_release"

    BUILD_DATE = "build_date"
    BUILD_HASH = "build_hash"
    HARDWARE_VERSION = "hardware_version"
    FIRMWARE_VERSION = "firmware_version"

    INPUT_SOURCE = "input_source"
    COMM_MODE = "communication_mode"
    COMMUNICATION_CHANNEL = "communication_channel"
    COMMUNICATION_PROTOCOL = "communication_protocol"
    TERMINATION = "termination"

    TIME_STAMP = "time_stamp"
    INDEX = "index"

