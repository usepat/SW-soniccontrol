from enum import IntEnum

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
    INTERNAL_COMMAND = 7
    # internal command of the device, that is not part of the protocol
    # the firmware uses this for internal commands, that should not be exposed to the user
    # this enum member just functions as a placeholder for the command code

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
    GET_ATF_LIST = 140
    GET_ATF = 141
    GET_TON = 150
    GET_ATK_LIST = 160
    GET_ATK = 161
    GET_ATT_LIST = 170
    GET_ATT = 171
    GET_SWF = 180
    GET_AUTO = 210
    GET_SCAN = 300
    GET_TUNE = 310
    GET_WIPE = 320
    GET_DUTY_CYCLE = 330

    SET_INPUT_SOURCE = 1010
    # = 1020
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

    SET_DEFAULT = 6000
    SET_FLASH_USB = 7001
    SET_FLASH_9600 = 7002
    SET_FLASH_115200 = 7003
    SET_NOTIFY = 999
    SET_DUTY_CYCLE = 8000
    SET_DUTY_CYCLE_T_OFF = 8001
    SET_DUTY_CYCLE_T_ON = 8002
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