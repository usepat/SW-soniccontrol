
from enum import unique
from sonic_protocol.schema import ICommandCode


@unique
class BaseCommandCode(ICommandCode):
    # first 100 commands reserved for base command codes
    GET_PROTOCOL = 0

    GET_INFO = 1

    GET_LOGGER_LIST_SIZE = 10
    GET_LOGGER_LIST_ITEM = 11
    SET_LOG_LEVEL = 12

    SET_DATETIME = 20
    GET_DATETIME = 21

    GET_ERROR_HISTO_SIZE = 30
    POP_ERROR_HISTO_MESSAGE = 31

    RESTART_DEVICE = 40 
    START_DIAGNOSTIC_TOOL = 41
    START_OPERATOR = 42
    START_CONFIGURATOR = 43
    START_CUSTOMIZER = 44

    SET_FLASH_USB = 50
    SET_FLASH_9600 = 51
    SET_FLASH_115200 = 52
    
    NOTIFY_MESSAGE = 18000

    # This allows to nest apis inside each other. 
    # Useful for using the command architecture also for internal commands that should not be exposed in the protocol
    # However it is cleaner to avoid this. TODO: remove this in the future
    INTERNAL_COMMAND = 19000 

    E_INTERNAL_DEVICE_ERROR = 20000
    E_COMMAND_NOT_KNOWN = 20001
    E_COMMAND_NOT_IMPLEMENTED = 20002
    E_COMMAND_NOT_PERMITTED = 20003
    E_COMMAND_INVALID = 20004
    E_SYNTAX_ERROR = 20005
    E_INVALID_VALUE = 20006
    E_PARSING_ERROR = 20007 
    E_TIMEOUT_ERROR = 20008


@unique
class CommandCode(ICommandCode):
    """!
    Command codes are the bridge between the commands implemented in python and c++ and the 
    CommandDefs in the generated CommandLookups from the protocol_builder.

    They are used as a unique identifier and to separate the protocol and definition logic,
    from the actual command and answer implementation.
    """
   # first 100 commands reserved for base command codes

    GET_PROTOCOL = BaseCommandCode.GET_PROTOCOL.value

    GET_INFO = BaseCommandCode.GET_INFO.value

    GET_LOGGER_LIST_SIZE = BaseCommandCode.GET_LOGGER_LIST_SIZE.value
    GET_LOGGER_LIST_ITEM = BaseCommandCode.GET_LOGGER_LIST_ITEM.value
    SET_LOG_LEVEL = BaseCommandCode.SET_LOG_LEVEL.value

    SET_DATETIME = BaseCommandCode.SET_DATETIME.value
    GET_DATETIME = BaseCommandCode.GET_DATETIME.value

    GET_ERROR_HISTO_SIZE = BaseCommandCode.GET_ERROR_HISTO_SIZE.value
    POP_ERROR_HISTO_MESSAGE = BaseCommandCode.POP_ERROR_HISTO_MESSAGE.value

    RESTART_DEVICE = BaseCommandCode.RESTART_DEVICE.value
    START_DIAGNOSTIC_TOOL = BaseCommandCode.START_DIAGNOSTIC_TOOL.value
    START_OPERATOR = BaseCommandCode.START_OPERATOR.value
    START_CONFIGURATOR = BaseCommandCode.START_CONFIGURATOR.value
    START_CUSTOMIZER = BaseCommandCode.START_CUSTOMIZER.value

    SET_FLASH_USB = BaseCommandCode.SET_FLASH_USB.value
    SET_FLASH_9600 = BaseCommandCode.SET_FLASH_9600.value
    SET_FLASH_115200 = BaseCommandCode.SET_FLASH_115200.value


    # 101 - 9999 are reserved for operator command codes

    # 101 - 199 are for update commands
    GET_UPDATE = 101
    GET_PROG_STATE = 102 # readable version of update
    GET_POSTMAN_UPDATE = 103 # update version for postman, needs only transducer state, signal, system_state, and device state
    GET_CONNECTION_STATUS = 104
    GET_UPDATE_WORKER_V3_0_0 = 105
    GET_UPDATE_DESCALE_V3_0_0 = 106

    # 200 - 399 are reserved for commands that involve the transducer directly
    GET_HELP = 200

    GET_SWF = 210
    SET_SWF = 211

    GET_FREQ = 220
    SET_FREQ = 221

    GET_ATF = 230
    SET_ATF = 231
    GET_ATF_LIST = 232

    GET_ATK = 240
    SET_ATK = 241
    GET_ATK_LIST = 242

    GET_ATT = 250
    SET_ATT = 251
    GET_ATT_LIST = 252

    GET_GAIN = 260
    SET_GAIN = 261

    GET_SIGNAL = 270
    SET_OFF = 271
    SET_ON = 272

    GET_WAVEFORM = 280
    SET_WAVEFORM = 281

    GET_TRANSDUCER_ID = 290
    SET_TRANSDUCER_ID = 291

    # measurements needed for experiments. Read only
    GET_TEMP = 300
    GET_TMCU = 301
    GET_UIPT = 302
    GET_UIPT_RAW = 303
    GET_IRMS = 304
    GET_ADC = 305

    GET_DAC = 310
    SET_DAC = 311


    # 400 - 500 is reserved for procedure commands

    GET_DUTY_CYCLE = 400
    SET_DUTY_CYCLE = 401
    SET_DUTY_CYCLE_T_OFF = 402
    SET_DUTY_CYCLE_T_ON = 403

    GET_RAMP = 410
    SET_RAMP = 411
    SET_RAMP_F_START = 412
    SET_RAMP_F_STOP = 413
    SET_RAMP_F_STEP = 414
    SET_RAMP_T_ON = 415
    SET_RAMP_T_OFF = 416
    SET_RAMP_GAIN = 417

    GET_SCAN = 420
    SET_SCAN = 421
    SET_SCAN_F_RANGE = 422 
    SET_SCAN_F_STEP = 423
    SET_SCAN_T_STEP = 424
    SET_SCAN_GAIN = 425
    SET_SCAN_F_SHIFT = 426

    GET_TUNE = 430
    SET_TUNE = 431
    SET_TUNE_F_STEP = 432
    SET_TUNE_T_TIME = 433
    SET_TUNE_T_STEP = 434
    SET_TUNE_F_SHIFT = 435
    SET_TUNE_N_STEPS = 436
    SET_TUNE_GAIN = 437

    GET_WIPE = 440
    SET_WIPE = 441
    SET_WIPE_F_RANGE = 442
    SET_WIPE_F_STEP = 443
    SET_WIPE_T_ON = 444
    SET_WIPE_T_OFF = 445
    SET_WIPE_T_PAUSE = 446
    SET_WIPE_GAIN = 447

    GET_AUTO = 450
    SET_AUTO = 451

    # everything afterwards is for general control and customization

    SET_STOP = 500
    SET_CONTINUE = 501
    SET_PAUSE = 502

    GET_NUM_TESTS = 510
    GET_TEST_INFO = 511
    GET_TEST_VALIDATION_ARG = 512
    RUN_TEST = 513
    ABORT_TEST = 514

    GET_MODBUS_SETTINGS = 520
    BROADCAST_MODBUS_SERVER_ID = 521
    SET_MODBUS_INTERFACE = 522
    SET_MODBUS_BAUDRATE = 523
    SET_MODBUS_PARITY = 524
    SET_MODBUS_SLAVE_ADDRESS = 525
    
    GET_CONTROL_MODE = 530
    SET_CONTROL_MODE = 531

    GET_ON_TIMER = 540
    RESET_ON_TIMER = 541

    SONIC_FORCE = 550

    GO_INTO_DEVICE_STATE = 560

    CLEAR_ERRORS = 570  # clears all errors currently only used by the device internal but later we will make this a legit command

    SET_COM_PROT = 580

    SET_TERMINATION = 590

    SET_DEFAULT = 600

    # can we delete those?
    # SET_PHYS_COM_CHANNEL = 2020 

    # commands from 18000 to 19000 are pure notifications

    NOTIFY_MESSAGE = BaseCommandCode.NOTIFY_MESSAGE.value
    NOTIFY_PROCEDURE_FAILURE = 18100

    # commands from 19000 are for debugging
    INTERNAL_COMMAND = BaseCommandCode.INTERNAL_COMMAND.value

    GET_DATETIME_PICO = 19030 

    # Error codes
    E_INTERNAL_DEVICE_ERROR = BaseCommandCode.E_INTERNAL_DEVICE_ERROR.value
    E_COMMAND_NOT_KNOWN = BaseCommandCode.E_COMMAND_NOT_KNOWN.value
    E_COMMAND_NOT_IMPLEMENTED = BaseCommandCode.E_COMMAND_NOT_IMPLEMENTED.value
    E_COMMAND_NOT_PERMITTED = BaseCommandCode.E_COMMAND_NOT_PERMITTED.value
    E_COMMAND_INVALID = BaseCommandCode.E_COMMAND_INVALID.value
    E_SYNTAX_ERROR = BaseCommandCode.E_SYNTAX_ERROR.value
    E_INVALID_VALUE = BaseCommandCode.E_INVALID_VALUE.value
    E_PARSING_ERROR = BaseCommandCode.E_PARSING_ERROR.value
    E_TIMEOUT_ERROR = BaseCommandCode.E_TIMEOUT_ERROR.value


    # Legacy commands. They are not really used for anything but for the device to select the correct command class
    LEGACY_AUTO = -1
    LEGACY_WIPE = -2
    LEGACY_STEP = -3
    LEGACY_SING = -4
    LEGACY_PAUS = -5
    LEGACY_RANG = -6
    LEGACY_TUST = -7
    LEGACY_TUTM = -8
    LEGACY_SCST = -9
    # WTF are those?
    LEGACY_PVAL = -10
    # GET_TON = 510

    # We do not know, if we still need those
    # SET_DAC0 = 5000
    # SET_DAC1 = 5010
    # SET_ATON = 5020
    # SET_TON = 5030
    # SET_TOFF = 5040 

