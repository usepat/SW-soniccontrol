from enum import unique
from sonic_protocol.schema import IEFieldName

@unique
class BaseFieldName(IEFieldName):
    # first 100 codes are reserved for base fields
    UNDEFINED = 0
    COMMAND_CODE = 1
    
    ERROR_MESSAGE = 2
    MESSAGE = 3

    UNKNOWN_ANSWER = 4
    SUCCESS = 5

    DEVICE_TYPE = 7
    PROTOCOL_VERSION = 8
    IS_RELEASE = 9
    ADDITIONAL_OPTIONS = 10

    BUILD_DATE = 11
    BUILD_HASH = 12
    HARDWARE_VERSION = 13
    FIRMWARE_VERSION = 14
    SNR = 15

    INDEX = 16
    COUNT = 17

    PASSWORD_HASHED = 18
    LOG_LEVEL = 19
    LOGGER_NAME = 20

    TIMESTAMP = 21

    ALLOCATOR_NAME = 22
    SIZE = 23
    CURRENT_USAGE = 24
    CURRENT_WASTED = 25
    CURRENT_ALLOCATIONS = 26
    WATERMARK_USAGE = 27
    WATERMARK_WASTED = 28
    WATERMARK_ALLOCATIONS = 29
    LIMIT = 30


@unique
class EFieldName(IEFieldName):
    UNDEFINED = BaseFieldName.UNDEFINED.value
    COMMAND_CODE = BaseFieldName.COMMAND_CODE.value
    
    ERROR_MESSAGE = BaseFieldName.ERROR_MESSAGE.value
    MESSAGE = BaseFieldName.MESSAGE.value
    UNKNOWN_ANSWER = BaseFieldName.UNKNOWN_ANSWER.value 

    SUCCESS = BaseFieldName.SUCCESS.value 

    DEVICE_TYPE = BaseFieldName.DEVICE_TYPE.value 
    PROTOCOL_VERSION = BaseFieldName.PROTOCOL_VERSION.value 
    IS_RELEASE = BaseFieldName.IS_RELEASE.value 
    ADDITIONAL_OPTIONS = BaseFieldName.ADDITIONAL_OPTIONS.value 

    BUILD_DATE = BaseFieldName.BUILD_DATE.value 
    BUILD_HASH = BaseFieldName.BUILD_HASH.value 
    HARDWARE_VERSION = BaseFieldName.HARDWARE_VERSION.value 
    FIRMWARE_VERSION = BaseFieldName.FIRMWARE_VERSION.value 
    SNR = BaseFieldName.SNR.value 

    INDEX = BaseFieldName.INDEX.value 
    COUNT = BaseFieldName.COUNT.value 

    PASSWORD_HASHED = BaseFieldName.PASSWORD_HASHED.value 
    LOG_LEVEL = BaseFieldName.LOG_LEVEL.value 
    LOGGER_NAME = BaseFieldName.LOGGER_NAME.value 

    TIMESTAMP = BaseFieldName.TIMESTAMP.value # never use this as a field. It gets set by sonic device

    ALLOCATOR_NAME = BaseFieldName.ALLOCATOR_NAME.value 
    SIZE = BaseFieldName.SIZE.value 
    CURRENT_USAGE = BaseFieldName.CURRENT_USAGE.value 
    CURRENT_WASTED = BaseFieldName.CURRENT_WASTED.value 
    CURRENT_ALLOCATIONS = BaseFieldName.CURRENT_ALLOCATIONS.value 
    WATERMARK_USAGE = BaseFieldName.WATERMARK_USAGE.value 
    WATERMARK_WASTED = BaseFieldName.WATERMARK_WASTED.value 
    WATERMARK_ALLOCATIONS = BaseFieldName.WATERMARK_ALLOCATIONS.value 
    LIMIT = BaseFieldName.LIMIT.value

    HELP = 106

    TRANSDUCER_ID = 112
    FREQUENCY = 113
    SWF = 114
    GAIN = 115
    TEMPERATURE = 116
    SIGNAL = 117
    WAVEFORM = 118
    URMS = 119
    IRMS = 120
    PHASE = 121
    TS_FLAG = 122
    PROCEDURE = 123
    PROCEDURE_ARG = 124
    ERROR_CODE = 125
    ANOMALY_DETECTION = 127
    VOLTAGE = 128
    TRANSDUCER_STATE = 129
    SYSTEM_STATE = 130

    TIMING = 131 # This field should not be used for answers or commands, it is provided by sonic_device for the Ping

    ATF = 132
    ATK = 133
    ATT = 134
    ATON = 135

    CONTROL_MODE = 141
    COMM_MODE = 142
    COMMUNICATION_CHANNEL = 143
    COMMUNICATION_PROTOCOL = 144
    TERMINATION = 145


    SCAN_F_CENTER = 147
    SCAN_F_RANGE = 148
    SCAN_F_STEP = 149
    SCAN_F_SHIFT = 150
    SCAN_T_STEP = 151
    SCAN_GAIN = 152
    TUNE_F_STEP = 153
    TUNE_F_SHIFT = 154
    TUNE_T_TIME = 155
    TUNE_T_STEP = 156
    TUNE_N_STEPS = 157
    TUNE_GAIN = 158
    WIPE_F_RANGE = 159
    WIPE_F_STEP = 160
    WIPE_T_ON = 161
    WIPE_T_OFF = 162
    WIPE_T_PAUSE = 163
    WIPE_GAIN = 164
    RAMP_F_START = 165
    RAMP_F_STOP = 166
    RAMP_F_STEP = 167
    RAMP_T_ON = 168
    RAMP_T_OFF = 169
    DUTY_CYCLE_T_OFF = 170
    DUTY_CYCLE_T_ON = 171

    # Legacy Fields
    LEGACY_RANG = 174
    LEGACY_STEP = 175
    LEGACY_SING = 176
    LEGACY_PAUS = 177
    LEGACY_TUST = 178
    LEGACY_TUTM = 179
    LEGACY_SCST = 180
    LEGACY_F_CENTER = 181
    LEGACY_POLL = 182

    MODBUS_SERVER_ID = 183

    DEVICE_STATE = 184

    MINUTES = 185
    HOURS = 186
    DAYS = 187

    RAMP_GAIN = 188

    IS_CONNECTED = 190
    TEST_NAME = 191
    TEST_SUITE_NAME = 192
    TEST_RESULT = 193
    TEST_INTERACTION = 194
    NUM_TEST_VALIDATION_ARGS = 195
    NAME = 196
    VALUE = 197
    TEST_STEP_INDEX = 198

    PARITY = 199
    UART_INTERFACE = 200
    BAUDRATE = 201

    IPP = 202

    

