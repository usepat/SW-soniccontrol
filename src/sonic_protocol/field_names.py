
from enum import unique
from sonic_protocol.defs import IEFieldName

@unique
class EFieldName(IEFieldName):
    UNDEFINED = "undefined"
    UNKNOWN_ANSWER = "unknown_answer"
    COMMAND_CODE = "command_code"
    SUCCESS = "success"
    
    HELP = "help"

    TRANSDUCER_ID = "transducer_id"
    FREQUENCY = "freq"
    SWF = "swf"
    GAIN = "gain"
    TEMPERATURE = "temp"
    SIGNAL = "signal"
    WAVEFORM = "waveform"
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
    ADDITIONAL_OPTIONS = "additional_options"

    BUILD_DATE = "build_date"
    BUILD_HASH = "build_hash"
    HARDWARE_VERSION = "hardware_version"
    FIRMWARE_VERSION = "firmware_version"

    INPUT_SOURCE = "input_source"
    COMM_MODE = "communication_mode"
    COMMUNICATION_CHANNEL = "communication_channel"
    COMMUNICATION_PROTOCOL = "communication_protocol"
    TERMINATION = "termination"

    TIMESTAMP = "timestamp"
    INDEX = "index"

    SCAN_F_CENTER = "scan_f_center"
    SCAN_F_RANGE = "scan_f_range"
    SCAN_F_STEP = "scan_f_step"
    SCAN_F_SHIFT = "scan_f_shift"
    SCAN_T_STEP = "scan_t_step"
    SCAN_GAIN = "scan_gain"
    TUNE_F_STEP = "tune_f_step"
    TUNE_F_SHIFT = "tune_f_shift"
    TUNE_T_TIME = "tune_t_time"
    TUNE_T_STEP = "tune_t_step"
    TUNE_N_STEPS = "tune_n_steps"
    TUNE_GAIN = "tune_gain"
    WIPE_F_RANGE = "wipe_f_range"
    WIPE_F_STEP = "wipe_f_step"
    WIPE_T_ON = "wipe_t_on"
    WIPE_T_OFF = "wipe_t_off"
    WIPE_T_PAUSE = "wipe_t_pause"
    RAMP_F_START = "ramp_f_start"
    RAMP_F_STOP = "ramp_f_stop"
    RAMP_F_STEP = "ramp_f_step"
    RAMP_T_ON = "ramp_t_on"
    RAMP_T_OFF = "ramp_t_off"
    DUTY_CYCLE_T_OFF = "duty_cycle_t_off"
    DUTY_CYCLE_T_ON = "duty_cycle_t_on"

    LOG_LEVEL = "log_level"
    LOGGER_NAME = "logger_name"

    # Legacy Fields
    LEGACY_RANG = "rang"
    LEGACY_STEP = "step"
    LEGACY_SING = "sing"
    LEGACY_PAUS = "paus"
    LEGACY_TUST = "tust"
    LEGACY_TUTM = "tutm"
    LEGACY_SCST = "scst"
    LEGACY_F_CENTER = "f_center"
    LEGACY_POLL = "polling_time"


