import platform
from pathlib import Path
from typing import Final

import attrs

# TODO: Better way to manage constants and test the directory reading
# TODO: Maybe consider moving few constants into a json config file


@attrs.frozen
class _Misc:
    ENCODING: Final[str] = "windows-1252" if platform.system() == "Windows" else "utf-8"
    IMAGE: Final[str] = "image"
    TEXT: Final[str] = "text"
    COMPOUND: Final[str] = "compound"
    BUTTON_ICON_SIZE: Final[tuple[int, int]] = (15, 15)
    TAB_ICON_SIZE: Final[tuple[int, int]] = (25, 25)


misc: _Misc = _Misc()


@attrs.frozen
class _Style:
    INVERSE_SECONDARY: Final[str] = "inverse-secondary"
    INVERSE_DANGER: Final[str] = "inverse-danger"
    DARK_OUTLINE_TOOLBUTTON: Final[str] = "dark-outline-toolbutton"


style: _Style = _Style()


@attrs.frozen
class _Files:
    # Paths
    SOURCE_DIR: Final[Path] = Path(__file__).parent.parent
    ROOT_DIR: Final[Path] = SOURCE_DIR.parent
    LOG_DIR: Final[Path] = ROOT_DIR / "logs"
    LOGGING_CONFIG: Final[Path] = LOG_DIR / "config.json"
    RESOURCES_DIR: Final[Path] = ROOT_DIR / "resources"
    PICTURES_DIR: Final[Path] = RESOURCES_DIR / "pictures"
    FONTS_DIR: Final[Path] = RESOURCES_DIR / "fonts"
    DOCUMENTS_DIR: Final[Path] = RESOURCES_DIR / "docs"
    CONFIG_JSON: Final[Path] = ROOT_DIR / "config.json"
    SONICCONTROL_LOG: Final[Path] = LOG_DIR / "soniccontrol.log"


files: _Files = _Files()


@attrs.frozen
class _Images:
    HOME_ICON_BLACK: Final[Path] = files.PICTURES_DIR / "home_icon_black.png"
    BACK_ICON_WHITE: Final[Path] = files.PICTURES_DIR / "back_icon_white.png"
    BACK_ICON_BLACK: Final[Path] = files.PICTURES_DIR / "back_icon_black.png"
    CONNECTION_ICON_BLACK: Final[Path] = (
        files.PICTURES_DIR / "connection_icon_black.png"
    )
    CONNECTION_ICON_WHITE: Final[Path] = (
        files.PICTURES_DIR / "connection_icon_white.png"
    )
    CONSOLE_ICON_BLACK: Final[Path] = files.PICTURES_DIR / "console_icon_black.png"
    SCRIPT_ICON_BLACK: Final[Path] = files.PICTURES_DIR / "script_icon_black.png"
    SETTINGS_ICON_BLACK: Final[Path] = files.PICTURES_DIR / "settings_icon_black.png"
    STATUS_ICON_BLACK: Final[Path] = files.PICTURES_DIR / "status_icon_black.png"
    FORWARDS_ICON_BLACK: Final[Path] = files.PICTURES_DIR / "forwards_icon_black.png"
    FORWARDS_ICON_WHITE: Final[Path] = files.PICTURES_DIR / "forwards_icon_white.png"
    INFO_ICON_BLACK: Final[Path] = files.PICTURES_DIR / "info_icon_black.png"
    INFO_ICON_WHITE: Final[Path] = files.PICTURES_DIR / "info_icon_white.png"
    LED_ICON_GREEN: Final[Path] = files.PICTURES_DIR / "led_green_icon.png"
    LED_ICON_RED: Final[Path] = files.PICTURES_DIR / "led_red_icon.png"
    LIGHTNING_ICON_WHITE: Final[Path] = files.PICTURES_DIR / "lightning_icon_white.png"
    LINECHART_ICON_BLACK: Final[Path] = files.PICTURES_DIR / "linechart_icon_black.png"
    MENUE_ICON_BLACK: Final[Path] = files.PICTURES_DIR / "menue_icon_black.png"
    MENUE_ICON_WHITE: Final[Path] = files.PICTURES_DIR / "menue_icon_white.png"
    PAUSE_ICON_BLACK: Final[Path] = files.PICTURES_DIR / "pause_icon_black.png"
    PAUSE_ICON_WHITE: Final[Path] = files.PICTURES_DIR / "pause_icon_white.png"
    PLAY_ICON_BLACK: Final[Path] = files.PICTURES_DIR / "play_icon_black.png"
    PLAY_ICON_WHITE: Final[Path] = files.PICTURES_DIR / "play_icon_white.png"
    REFRESH_ICON_WHITE: Final[Path] = files.PICTURES_DIR / "refresh_icon_white.png"
    REFRESH_ICON_BLACK: Final[Path] = files.PICTURES_DIR / "refresh_icon_black.png"
    REFRESH_ICON_GREY: Final[Path] = files.PICTURES_DIR / "refresh_icon_grey.png"
    RESET_ICON_BLACK: Final[Path] = files.PICTURES_DIR / "reset_icon_black.png"
    RESET_ICON_WHITE: Final[Path] = files.PICTURES_DIR / "reset_icon_white.png"
    SAVE_ICON_BLACK: Final[Path] = files.PICTURES_DIR / "save_icon_black.png"
    SAVE_ICON_WHITE: Final[Path] = files.PICTURES_DIR / "save_icon_white.png"


images: _Images = _Images()


@attrs.frozen
class _Fonts:
    QTYPE_OT_COND_EXTRALIGHT_PATH: Final[Path] = (
        files.FONTS_DIR / "QTypeOT-CondExtraLight.otf"
    )


fonts: _Fonts = _Fonts()


@attrs.frozen
class _Events:
    # Events
    RESIZING_EVENT: Final = "<Configure>"
    CONNECTION_ATTEMPT_EVENT: Final = "<<ConnectionAttempt>>"
    DISCONNECTED_EVENT: Final = "<<Disconnected>>"
    SCRIPT_START_EVENT: Final = "<<ScriptStarted>>"
    SCRIPT_STOP_EVENT: Final = "<<ScriptStopped>>"
    FIRMWARE_FLASH_EVENT: Final = "<<FirmwareFlash>>"
    SONICMEASURE_START_EVENT: Final = "<<SonicMeasureStarted>>"
    SONICMEASURE_STOP_EVENT: Final = "<<SonicMeasureStopped>>"
    STATUS_UPDATE_EVENT: Final = "<<StatusUpdate>>"
    MANUAL_MODE_EVENT: Final = "<<ManualMode>>"
    AUTO_MODE_EVENT: Final = "<<AutoMode>>"


events: _Events = _Events()


@attrs.frozen
class _UIStringsEN:
    HOME_CONTROL_LABEL: Final[str] = "Manual Control"
    FREQ_PLACEHOLDER: Final[str] = "Set Frequency..."
    GAIN_PLACEHOLDER: Final[str] = "Set Gain..."
    SAVE_LABEL: Final[str] = "Save"
    START_LABEL: Final[str] = "Start"
    PAUSE_LABEL: Final[str] = "Pause"
    CONNECT_LABEL: Final[str] = "Connect"
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
    SONIC_LABEL: Final[str] = "sonic"
    SONIC_MEASURE_LABEL: Final[str] = "Sonic Measure"
    SPECIFY_PATH_LABEL: Final[str] = "Specify Path"
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
    SEND_LABEL: Final[str] = "Send"
    THEME: Final[str] = "sandstone"
    IDLE_TITLE: Final[str] = "Sonic Control"
    AUTO_READ_LABEL: Final[str] = "Auto Read"
    BACK_LABEL: Final[str] = "Back"
    FLASH_SETTINGS_LABEL: Final[str] = "Flash Firmware Settings"
    SONICAMP_SETTINGS_LABEL: Final[str] = "SonicAmp Settings"
    SONICCONTROL_SETTINGS_LABEL: Final[str] = "SonicControl Settings"
    SUBMIT_LABEL: Final[str] = "Submit"
    CONTROL_LABEL: Final[str] = "control"
    COMPANY_NAME: Final[str] = "usePAT G.m.b.H"
    VERSION_LABEL: Final[str] = "Version"


ui: _UIStringsEN = _UIStringsEN()
