import attrs
from pathlib import Path
from importlib import resources as rs
import soniccontrol_gui

@attrs.frozen
class _Resources:
    LOGGING_CONFIG = Path(str(rs.files(soniccontrol_gui).joinpath("log_config.json")))
    RESOURCES = rs.files("soniccontrol_gui.resources")
    PICTURES = rs.files("soniccontrol_gui.resources.pictures")
    FONTS = rs.files("soniccontrol_gui.resources.fonts")
    TEXTS = rs.files("soniccontrol_gui.resources.texts")
    HELPTEXT_INTERNAL_COMMANDS = Path(str(TEXTS.joinpath("helptext_internal_commands.md")))


resources: _Resources = _Resources()

@attrs.frozen
class _Images:
    HOME_ICON_BLACK = "home_icon_black.png"
    BACK_ICON_WHITE = "back_icon_white.png"
    BACK_ICON_BLACK = "back_icon_black.png"
    CONNECTION_ICON_BLACK = "connection_icon_black.png"
    CONNECTION_ICON_WHITE = "connection_icon_white.png"
    CONSOLE_ICON_BLACK = "console_icon_black.png"
    SCRIPT_ICON_BLACK = "script_icon_black.png"
    SETTINGS_ICON_BLACK = "settings_icon_black.png"
    STATUS_ICON_BLACK = "status_icon_black.png"
    FORWARDS_ICON_BLACK = "forwards_icon_black.png"
    FORWARDS_ICON_WHITE = "forwards_icon_white.png"
    INFO_ICON_BLACK = "info_icon_black.png"
    INFO_ICON_WHITE = "info_icon_white.png"
    LED_ICON_GREEN = "led_green_icon.png"
    LED_ICON_RED = "led_red_icon.png"
    LIGHTNING_ICON_WHITE = "lightning_icon_white.png"
    LINECHART_ICON_BLACK = "linechart_icon_black.png"
    MENUE_ICON_BLACK = "menue_icon_black.png"
    MENUE_ICON_WHITE = "menue_icon_white.png"
    PAUSE_ICON_BLACK = "pause_icon_black.png"
    PAUSE_ICON_WHITE = "pause_icon_white.png"
    PLAY_ICON_BLACK = "play_icon_black.png"
    PLAY_ICON_WHITE = "play_icon_white.png"
    REFRESH_ICON_WHITE = "refresh_icon_white.png"
    REFRESH_ICON_BLACK = "refresh_icon_black.png"
    REFRESH_ICON_GREY = "refresh_icon_grey.png"
    SAVE_ICON_BLACK = "save_icon_black.png"
    SAVE_ICON_WHITE = "save_icon_white.png"
    END_ICON_WHITE = "end_icon_white.png"
    END_ICON_BLACK = "end_icon_black.png"
    
    LOGO = "usepat_neu-4c-mSL.png"

    HOME_CONTROL_PANEL = "home_control_panel.png"
    HOME_SIGNAL_CONTROL_PANEL = "home_signal_control_panel.png"


images: _Images = _Images()