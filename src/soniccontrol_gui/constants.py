from typing import Final, List, Literal

import attrs

from soniccontrol.app_config import APP_DATA_DIR, SONIC_CONTROL_BASE_DIR
from soniccontrol_gui.utils.types import ScriptingGuideCardDataDict
from soniccontrol.events import PropertyChangeEvent
from soniccontrol.procedures.procedure_controller import ProcedureController


@attrs.frozen
class _TkinterConstants:
    WRITE: Literal["write"] = "write"
    READ: Literal["read"] = "read"
    IMAGE: Literal["image"] = "image"
    COMPOUND: Literal["compound"] = "compound"
    DELETE_WINDOW: Literal["WM_DELETE_WINDOW"] = "WM_DELETE_WINDOW"


tk_const: Final[_TkinterConstants] = _TkinterConstants()


@attrs.frozen
class _Files:
    DATA_DIR =  APP_DATA_DIR
    LOG_DIR = DATA_DIR / "logs"
    MEASUREMENTS_DIR = DATA_DIR / "measurements"
    TRANSDUCER_CONFIG_FOLDER = DATA_DIR / "transducer_configs"
    LEGACY_TRANSDUCER_CONFIG_FOLDER = DATA_DIR / "legacy_transducer_configs"
    LEGACY_TRANSDUCER_CONFIG_JSON = LEGACY_TRANSDUCER_CONFIG_FOLDER / "template.json"
    TRANSDUCER_CONFIG_JSON = TRANSDUCER_CONFIG_FOLDER / "template.json"
    EXPERIMENT_TEMPLATES_JSON = DATA_DIR / "experiment_templates.json"
    SONICCONTROL_LOG = LOG_DIR / "soniccontrol.log"
    SCRIPT_DIR = DATA_DIR / "scripts"
    EXAMPLE_SCRIPT = SCRIPT_DIR / "example_script"
    EXAMPLE_SCRIPT_DIR = SONIC_CONTROL_BASE_DIR / "sonic_script_examples"

files: _Files = _Files()

@attrs.frozen
class _Fonts:
    QTYPE_OT: Literal["QTypeOT"] = "QTypeOT"
    QTYPE_OT_CONDLIGHT: Literal["QTypeOT-CondLight"] = "QTypeOT-CondLight"
    HEADING_SIZE: Final[int] = 24
    TEXT_SIZE: Final[int] = 10
    SMALL_HEADING_SIZE: Final[int] = 15


fonts: _Fonts = _Fonts()


@attrs.frozen
class _Sizes:
    BUTTON_ICON_SIZE: Final[tuple[int, int]] = (15, 15)
    LARGE_BUTTON_ICON_SIZE: Final[tuple[int, int]] = (20, 20)
    TAB_ICON_SIZE: Final[tuple[int, int]] = (25, 25)
    SMALL_PADDING: Final[int] = 3
    SMALL_PART_PADDING: Final[int] = 2
    MEDIUM_PADDING: Final[int] = 5
    LARGE_PART_PADDING: Final[int] = 7
    LARGE_PADDING: Final[int] = 10
    SIDE_PADDING: Final[int] = 15
    DONT_EXPAND: Final[int] = 0
    EXPAND: Final[int] = 1
    METERSIZE: Final[int] = 130


sizes: Final[_Sizes] = _Sizes()


@attrs.frozen
class _Color:
    DARK_GREEN: Literal["green"] = "green"
    STATUS_MEDIUM_GREY: Literal["#c3c0ba"] = "#c3c0ba"
    STATUS_LIGHT_GREY: Literal["#f8f5f0"] = "#f8f5f0"


color: Final[_Color] = _Color()


@attrs.frozen
class _Style:
    SECONDARY_OUTLINE: Literal["secondary-outline"] = "secondary-outline"
    INVERSE_SECONDARY: Literal["inverse-secondary"] = "inverse-secondary"
    INVERSE_PRIMARY: Literal["inverse-primary"] = "inverse-primary"
    INVERSE_SUCCESS: Literal["inverse-success"] = "inverse-success"
    INVERSE_LIGHT: Literal["inverse-light"] = "inverse-light"
    INVERSE_DANGER: Literal["inverse-danger"] = "inverse-danger"
    DARK_OUTLINE_TOOLBUTTON: Literal[
        "dark-outline-toolbutton"
    ] = "dark-outline-toolbutton"
    DARK_SQUARE_TOGGLE: Literal["dark-square-toggle"] = "dark-square-toggle"


style: Final[_Style] = _Style()


@attrs.frozen
class _UIStringsEN:
    CONFIGURATION_TAB: Final[str] = "Configuration"
    UPDATER_INTERVAL_LABEL: Final[str] = "Updater Interval (ms):"
    IS_LEGACY_DEVICE_LABEL: Final[str] = "SonicCrystal"
    HOME_CONTROL_LABEL: Final[str] = "Manual Control"
    FREQ_PLACEHOLDER: Final[str] = "Set Frequency..."
    GAIN_PLACEHOLDER: Final[str] = "Set Gain..."
    APPLY_SETTINGS: Final[str] = "Apply Settings"
    SAVE_LABEL: Final[str] = "Save"
    SAVE_AS_LABEL: Final[str] = "Save As"
    SAVE_PLOT_LABEL: Final[str] = "Save Plot"
    CSV_TAB_TITLE: Final[str] = "Csv"
    START_LABEL: Final[str] = "Start"
    END_LABEL: Final[str] = "End"
    STOP_LABEL: Final[str] = "Stop"
    PAUSE_LABEL: Final[str] = "Pause"
    RESUME_LABEL: Final[str] = "Resume"
    SINGLE_STEP_LABEL: Final[str] = "Single Step"
    CONNECT_LABEL: Final[str] = "Connect"
    CONNECT_TO_SIMULATION_LABEL: Final[str] = "Connect To Simulation"
    DISCONNECT_LABEL: Final[str] = "Disconnect"
    HOME_LABEL: Final[str] = "Home"
    SCRIPTING_LABEL: Final[str] = "Scripting"
    CONNECTION_LABEL: Final[str] = "Connection"
    CONNECTED_LABEL: Final[str] = "connected"
    NOT_LABEL: Final[str] = "not"
    FIRMWARE_LABEL: Final[str] = "Firmware"
    PLEASE_CONNECT_LABEL: Final[str] = "Please connect to a sonicamp system"
    SETTINGS_LABEL: Final[str] = "Settings"
    INFO_LABEL: Final[str] = "Info"
    SERIAL_MONITOR_LABEL: Final[str] = "Serial Monitor"
    LOGS_LABEL: Final[str] = "Logs"
    APP_LOGS_LABEL: Final[str] = "Application Logs"
    DEVICE_LOGS_LABEL: Final[str] = "Device Logs"
    FLASHER_LABEL: Final[str] = "Flasher"
    PROCEDURES_LABEL: Final[str] = "Procedures"
    SONIC_LABEL: Final[str] = "sonic"
    SPECTRUM_MEASURE_TITLE: Final[str] = "Spectrum Measure"
    SONIC_MEASURE_LABEL: Final[str] = "Sonic Measure"
    NEW_EXPERIMENT: Final[str] = "New Experiment"
    SPECIFY_PATH_LABEL: Final[str] = "Specify Path"
    SEARCH: Final[str] = "Search:"
    SET_FREQUENCY_LABEL: Final[str] = "Set Frequency"
    SET_GAIN_LABEL: Final[str] = "Set Gain"
    ON_LABEL: Final[str] = "ON"
    OFF_LABEL: Final[str] = "OFF"
    AUTO_LABEL: Final[str] = "AUTO"
    CATCH_MODE_LABEL: Final[str] = "Catch Mode"
    CATCH_LABEL: Final[str] = "Catch"
    WIPE_MODE_LABEL: Final[str] = "Wipe Mode"
    WIPE_LABEL: Final[str] = "Wipe"
    SET_VALUES_LABEL: Final[str] = "Set Values"
    OUTPUT_LABEL: Final[str] = "Output"
    INPUT_LABEL: Final[str] = "Input"
    GUIDE_LABEL: Final[str] = "Guide"
    SCRIPT_EDITOR_LABEL: Final[str] = "Script Editor"
    LOAD_LABEL: Final[str] = "Load File"
    LOAD_EXAMPLE_LABEL: Final[str] = "Load Example"
    SEND_LABEL: Final[str] = "Send"
    DELETE_LABEL: Final[str] = "Delete"
    FINISH_LABEL: Final[str] = "Finish"
    THEME: Final[str] = "sandstone"
    IDLE_TITLE: Final[str] = "Sonic Control"
    AUTO_READ_LABEL: Final[str] = "Auto Read"
    BACK_LABEL: Final[str] = "Back"
    FLASH_SETTINGS_LABEL: Final[str] = "Flash Firmware Settings"
    SONICAMP_SETTINGS_LABEL: Final[str] = "SonicDevice Settings"
    SONICCONTROL_SETTINGS_LABEL: Final[str] = "SonicControl Settings"
    SUBMIT_LABEL: Final[str] = "Submit"
    SELECTED: Final[str] = "Selected"
    CONTROL_LABEL: Final[str] = "control"
    COMPANY_NAME: Final[str] = "usePAT G.m.b.H"
    VERSION_LABEL: Final[str] = "Version"
    ATK: Final[str] = "ATK"
    ATF: Final[str] = "ATF"
    ATT: Final[str] = "ATT"
    COEFFICIENT: Final[str] = "Coefficient"
    FREQUENCY: Final[str] = "Frequency"
    SWITCHING_FREQUENCY: Final[str] = "Switching Frequency"
    GAIN: Final[str] = "Gain"
    TEMPERATURE: Final[str] = "Temperature"
    ATF1: Final[str] = f"{ATF}1 {FREQUENCY}"
    ATF2: Final[str] = f"{ATF}2 {FREQUENCY}"
    ATF3: Final[str] = f"{ATF}3 {FREQUENCY}"
    ATK1: Final[str] = f"{ATK}1 {COEFFICIENT}"
    ATK2: Final[str] = f"{ATK}2 {COEFFICIENT}"
    ATK3: Final[str] = f"{ATK}3 {COEFFICIENT}"
    ATT1: Final[str] = f"{ATT} {TEMPERATURE}"
    KHZ: Final[str] = "kHz"
    DEGREE_CELSIUS: Final[str] = "°C"
    PERCENT: Final[str] = "%"
    SIGNAL_LABEL: Final[str] = "Signal"
    SIGNAL_OFF: Final[str] = f"{SIGNAL_LABEL} {OFF_LABEL}"
    SIGNAL_ON: Final[str] = f"{SIGNAL_LABEL} {ON_LABEL}"
    NOT_CONNECTED: Final[str] = f"{NOT_LABEL} {CONNECTED_LABEL}"
    RESTART: Final[str] = "Restart"
    END: Final[str] = "End"
    LIVE_PLOT: Final[str] = "Live Plot"
    URMS: Final[str] = "Urms"
    IRMS: Final[str] = "Irms"  
    PHASE: Final[str] = "Phase"
    START_LIVE_PLOT: Final[str] = f"{START_LABEL} {LIVE_PLOT}"
    START_VALUE: Final[str] = "Start value:"
    STOP_VALUE: Final[str] = "Stop value:"
    STEP_VALUE: Final[str] = "Step value:"
    ON_DURATION: Final[str] = "On duration:"
    OFF_DURATION: Final[str] = "Off duration:"
    USE_SCRIPTING_INSTEAD: Final[str] = "Use scripting instead"
    COMMAND_SET: Final[str] = "Command set"
    NEW_LABEL: Final[str] = "New"
    IMPORT_LABEL: Final[str] = "Import"
    DATA_VISUALIZER: Final[str] = "Data Visualizer"
    REFRESH: Final[str] = "Refresh"
    VISUALIZE: Final[str] = "Visualize"
    HOME_HELP_INTRODUCTION: Final[
        str
    ] = "The Home tab is used to set the most important parameters of a Sonicamp device manually."
    HOME_HELP_CONTROL_PANEL: Final[
        str
    ] = "The Manual Control Panel contains entries to set the named parameters. Based on your Sonicamp those parameters may differ from the shown image."
    HOME_HELP_FREQUENCY: Final[
        str
    ] = ""#"Here should be a description of the frequency entry."
    HOME_HELP_GAIN: Final[str] = ""#"Here should be a description of the gain entry."
    HOME_HELP_CATCH: Final[str] = ""#"Here should be a description of the catch entry."
    HOME_HELP_WIPE: Final[str] = ""#"Here should be a description of the wipe entry."
    HOME_HELP_SET_VALUES: Final[
        str
    ] = "The 'Set Values' button sets all currently configured parameters."
    HOME_HELP_OUTPUT: Final[
        str
    ] = "The Sonicamp device sends it's answer to the requested configuration in the Feedback frame."
    HOME_HELP_SIGNAL_CONTROL_PANEL: Final[
        str
    ] = "The signal of the Sonicamp device can be set to ON, AUTO or OFF."
    HOME_HELP_ON: Final[str] = ""#"Here should be a description of the on entry."
    HOME_HELP_AUTO: Final[str] = ""#"Here should be a description of the auto entry."
    HOME_HELP_OFF: Final[str] = ""#"Here should be a description of the off entry."
    CHOOSE_A_CAPTURE_TARGET: Final[str] = "Choose a capture target"
    START_CAPTURE: Final[str] = "Start Capture"
    END_CAPTURE: Final[str] = "End Capture"
    PROC_RUNNING: Final[str] = "Procedure [{}] is running..."
    PROC_NOT_RUNNING: Final[str] = "No Procedure running"
    DEVICE_DISCONNECTED_TITLE: Final[str] = "Device disconnected"
    DEVICE_DISCONNECTED_MSG: Final[str] = "The device got disconnected, Do you want to close this window?"
    COULD_NOT_CONNECT_MESSAGE: Final[str] = "Could not connected due to error:\n{}\nDo you want to open the rescue mode?"
    FIRMWARE_VERSION_LABEL: Final[str] = "Firmware Version: {}"
    PROTOCOL_VERSION_LABEL: Final[str] = "Protocol Version: {}"
    DEVICE_TYPE_LABEL: Final[str] = "Device Type: {}"
    DEVICE_FLASHED_TITLE: Final[str] = "Device flashing"
    DEVICE_FLASHED_SUCCESS_MSG: Final[str] = "Device was successfully flashed, restart device and soniccontrol"
    DEVICE_FLASHED_FAILED_MSG: Final[str] = "Flashing the device failed, restart soniccontrol"
    FLASH_LEGACY: Final[str] = "FLASH_LEGACY"
    FLASH_UART_SLOW: Final[str] = "FLASH_UART_SLOW"
    FLASH_UART_FAST: Final[str] = "FLASH_UART_FAST"
    FLASH_USB: Final[str] = "FLASH_USB"
    OPEN_LOGS: Final[str] = "Open Logs"
    GO_TO_MEASUREMENTS: Final[str] = "Go to Measurements"
    FORM_ADD_ENTRY: Final[str] = "Add Entry"
    CONFIGURING_LABEL: Final[str] = "configuring device"
    WAITING_FOR_ANSWER: Final[str] = "Waiting for answer"
    START_CONFIGURATOR: Final[str] = "--start-configurator"


ui_labels: Final[_UIStringsEN] = _UIStringsEN()


@attrs.frozen
class _Events:
    CLICKED_EVENT: Literal["<Button-1>"] = "<Button-1>"
    RESIZING_EVENT: Literal["<Configure>"] = "<Configure>"
    CONNECTION_ATTEMPT_EVENT: Literal["<<ConnectionAttempt>>"] = "<<ConnectionAttempt>>"
    CONNECTED_EVENT: Literal["<<Connected>>"] = "<<Connected>>"
    DISCONNECTED_EVENT: Literal["<<Disconnected>>"] = "<<Disconnected>>"
    SCRIPT_START_EVENT: Literal["<<ScriptStarted>>"] = "<<ScriptStarted>>"
    SCRIPT_STOP_EVENT: Literal["<<ScriptStopped>>"] = "<<ScriptStopped>>"
    FIRMWARE_FLASH_EVENT: Literal["<<FirmwareFlash>>"] = "<<FirmwareFlash>>"
    SONICMEASURE_START_EVENT: Literal[
        "<<SonicMeasureStarted>>"
    ] = "<<SonicMeasureStarted>>"
    SONICMEASURE_STOP_EVENT: Literal[
        "<<SonicMeasureStopped>>"
    ] = "<<SonicMeasureStopped>>"
    SCRIPT_PAUSE_EVENT: Literal["<<ScriptPause>>"] = "<<ScriptPause>>"
    STATUS_UPDATE_EVENT: Literal["<<StatusUpdate>>"] = "<<StatusUpdate>>"
    MANUAL_MODE_EVENT: Literal["<<ManualMode>>"] = "<<ManualMode>>"
    AUTO_MODE_EVENT: Literal["<<AutoMode>>"] = "<<AutoMode>>"
    SIGNAL_OFF: Literal["<<SignalOff>>"] = "<<SignalOff>>"
    SIGNAL_ON: Literal["<<SignalOn>>"] = "<<SignalOn>>"
    SAVE_CONFIG: Literal["<<SaveConfig>>"] = "<<SaveConfig>>"
    PROPERTY_CHANGE_EVENT = PropertyChangeEvent.PROPERTY_CHANGE_EVENT
    PROCEDURE_RUNNING = ProcedureController.PROCEDURE_RUNNING
    PROCEDURE_STOPPED = ProcedureController.PROCEDURE_STOPPED

events: Final[_Events] = _Events()



scripting_cards_data: Final[List[ScriptingGuideCardDataDict]] = [
    {
        "keyword": "on",
        "arguments": "None",
        "description": "Sets the signal to ON",
        "example": "on",
    },
    {
        "keyword": "off",
        "arguments": "None",
        "description": "Set the signal to OFF",
        "example": "off",
    },
    {
        "keyword": "frequency",
        "arguments": "frequency: uint",
        "description": "Set the frequency of the device",
        "example": "frequency 1000000",
    },
    {
        "keyword": "gain",
        "arguments": "gain: uint",
        "description": "Set the Gain of the device",
        "example": "gain 100",
    },
    {
        "keyword": "hold",
        "arguments": "hold: time",
        "description": "holds execution for an amount of time",
        "example": "hold 500ms",
    },
        {
        "keyword": "send",
        "arguments": "command_string: str",
        "description": "Sends a command to the device, directly over the serial communication",
        "example": "send \"!frequency=100000\"",
    },
    {
        "keyword": "loop",
        "arguments": "n: uint",
        "description": "Repeats a block of code n times",
        "example": 
"""loop 5 times
begin
    # code
end""",
    },   
    {
        "keyword": "breakpoint",
        "arguments": "None",
        "description": "Pauses execution. Nice for debugging",
        "example": """loop 5 times
begin
    on
    breakpoint // pauses execution
    off
end""",
    },
    {
        "keyword": "ramp",
        "arguments": "f_start: uint\nf_stop: uint\nf_step: uint\nt_on: time\nt_off: time",
        "description": "Executes the ramp procedure",
        "example": "ramp 1000000 2000000 100000 1s 500ms",
    },
    {
        "keyword": "wipe",
        "arguments": "f_range: uint\nf_step: uint\nt_on: time\nt_off: time\nt_pause: time",
        "description": "Executes the wipe procedure",
        "example": "wipe 8000 1000 500ms 20ms 2s",
    },
    {
        "keyword": "scan",
        "arguments": "f_center: uint\ngain: uint\nf_range: uint\nf_step: uint\nf_shift: uint\nt_step: time",
        "description": "Executes the scan procedure",
        "example": "scan 1000000 20 8000 1000 0 100ms",
    },
    {
        "keyword": "tune",#TODO add gain for the next procotol version
        "arguments": "f_step: uint\nt_time: time\nn_steps: uint\nf_shift: uint\nt_step: time",
        "description": "Executes the tune procedure",
        "example": "tune 1000 5000ms 3 0 100ms",
    },
    {
        "keyword": "auto",
        "arguments": "scan_f_center: uint\nscan_gain: uint\nscan_f_range: uint\nscan_f_step: uint\nscan_f_shift: uint\nscan_t_step: time\ntune_f_step: uint\ntune_t_time: time\ntune_n_steps: uint\ntune_f_shift: uint\ntune_t_step: time",
        "description": "Executes the auto procedure",
        "example": "auto 1000000 20 8000 1000 0 100ms 1000 5000ms 3 0 100ms",
    },
    {
        "keyword": "auto_legacy",
        "arguments": "f_center: uint\ntust: uint\ntutm: time\nscst: uint\n",
        "description": "Executes the auto procedure",
        "example": "auto_legacy 1000000 500 10000ms 1000",
    },
    {
        "keyword": "wipe_legacy",
        "arguments": "step: uint\nsing: time\npaus: time\nrang: uint",
        "description": "Executes the wipe procedure",
        "example": "wipe_legacy 500 500ms 1000ms 8000",
    },
]
