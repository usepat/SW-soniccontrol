
from enum import unique
from sonic_protocol.schema import ICommandCode


@unique
class BaseCommandCode(ICommandCode):
    NOTIFY_MESSAGE = 18000

    # This allows to nest apis inside each other. 
    # Useful for using the command architecture also for internal commands that should not be exposed in the protocol
    INTERNAL_COMMAND = 19030 

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

    GET_PROTOCOL = 0
    GET_INFO = 1
    GET_HELP = 2
    GET_UPDATE = 3
    GET_PROG_STATE = 4 # readable version of update
    GET_POSTMAN_UPDATE = 5 # update version for postman, needs only transducer state, signal, system_state, and device state
    
    # Those commands have a corresponding setter command
    GET_SWF = 10
    GET_FREQ = 20
    GET_GAIN = 30
    GET_TRANSDUCER_ID = 90

    GET_ATF = 101
    GET_ATK = 111
    GET_ATT = 121

    # Those codes are only needed for isValidCode implementation
    GET_ATF2 = 102
    GET_ATF3 = 103
    GET_ATF4 = 104
    GET_ATK2 = 112
    GET_ATK3 = 113
    GET_ATK4 = 114
    GET_ATT2 = 122
    GET_ATT3 = 123
    GET_ATT4 = 124

    GET_DATETIME = 130
    GET_WAVEFORM = 140
    GET_LOG_LEVEL = 150


    # THOSE ONES DO NOT HAVE A corresponding setter
    GET_SIGNAL = 40
    GET_TEMP = 50
    GET_TMCU = 60
    GET_UIPT = 70
    GET_IRMS = 80
    
    GET_ATF_LIST = 100
    GET_ATK_LIST = 110
    GET_ATT_LIST = 120

    GET_DUTY_CYCLE = 300
    GET_RAMP = 310
    GET_SCAN = 320
    GET_TUNE = 330
    GET_WIPE = 340
    GET_AUTO = 350
    GET_ADC = 360
    GET_CONTROL_MODE = 370
    GET_ERROR_HISTO_SIZE = 380
    GET_DAC = 390
    # GET_MODBUS_SERVER_ID = 400

    # Setters with corresponding getters
    SET_SWF = 1010
    SET_FREQ = 1020
    SET_GAIN = 1030
    SET_TRANSDUCER_ID = 1090

    SET_ATF = 1101
    SET_ATK = 1111
    SET_ATT = 1121

    # Those codes are only needed for isValidCode implementation
    SET_ATF2 = 1102
    SET_ATF3 = 1103
    SET_ATF4 = 1104
    SET_ATK2 = 1112
    SET_ATK3 = 1113
    SET_ATK4 = 1114
    SET_ATT2 = 1122
    SET_ATT3 = 1123
    SET_ATT4 = 1124

    SET_DATETIME = 1130
    SET_WAVEFORM = 1140
    SET_LOG_LEVEL = 1150

    SET_DEFAULT = 9000

    # Setters with no corresponding getters
    SET_OFF = 1040
    SET_ON = 1041

    SET_DUTY_CYCLE_T_OFF = 1301
    SET_DUTY_CYCLE_T_ON = 1302
    SET_RAMP_F_START = 1311
    SET_RAMP_F_STOP = 1312
    SET_RAMP_F_STEP = 1313
    SET_RAMP_T_ON = 1314
    SET_RAMP_T_OFF = 1315
    SET_SCAN_F_RANGE = 1321 
    SET_SCAN_F_STEP = 1322
    SET_SCAN_T_STEP = 1323
    SET_SCAN_GAIN = 1324
    SET_SCAN_F_SHIFT = 1325
    SET_TUNE_F_STEP = 1331
    SET_TUNE_T_TIME = 1332
    SET_TUNE_T_STEP = 1333
    SET_TUNE_F_SHIFT = 1334
    SET_TUNE_N_STEPS = 1335
    SET_TUNE_GAIN = 1336
    SET_WIPE_F_RANGE = 1341
    SET_WIPE_F_STEP = 1342
    SET_WIPE_T_ON = 1343
    SET_WIPE_T_OFF = 1344
    SET_WIPE_T_PAUSE = 1345
    SET_WIPE_GAIN = 1346

    SET_DAC = 1390
    # SET_MODBUS_SERVER_ID = 1400

    
    SET_CONTROL_MODE = 2000
    SET_COM_PROT = 2010
    SET_PHYS_COM_CHANNEL = 2020 
    SET_TERMINATION = 2030
    CLEAR_ERRORS = 2040  # clears all errors currently only used by the device internal but later we will make this a legit command
    POP_ERROR_HISTO_MESSAGE = 2050
    BROADCAST_MODBUS_SERVER_ID = 2060
    

    # commands that execute something

    SET_DUTY_CYCLE = 1300
    SET_RAMP = 1310
    SET_SCAN = 1320
    SET_TUNE = 1330
    SET_WIPE = 1340
    SET_AUTO = 1350

    SET_STOP = 3000
    SET_CONTINUE = 3010
    SET_PAUSE = 3020

    SET_FLASH_USB = 7001
    SET_FLASH_9600 = 7002
    SET_FLASH_115200 = 7003
    START_CONFIGURATOR = 8000


    # commands from 18000 to 19000 are pure notifications

    NOTIFY_MESSAGE = BaseCommandCode.NOTIFY_MESSAGE.value
    # NOTIFY_TUNE = 18001
    NOTIFY_PROCEDURE_FAILURE = 18100

    # commands from 19000 are for debugging
    GET_DATETIME_PICO = 19000 
    RESTART_DEVICE = 19010

    INTERNAL_COMMAND = BaseCommandCode.INTERNAL_COMMAND.value
    SONIC_FORCE = 19040
    GO_INTO_DEVICE_STATE = 19050

    # internal command of the device, that is not part of the protocol
    # the firmware uses this for internal commands, that should not be exposed to the user
    # this enum member just functions as a placeholder for the command code

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

