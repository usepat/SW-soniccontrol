from enum import Enum
import os
from pathlib import Path
import sys
from typing import Final
from sonic_protocol.defs import Version
from importlib.metadata import version
import re


def get_version_tag() -> str:
    version_desc = version("soniccontrol")
    regex = r"v?(?P<tag>\d+\.\d+\.\d+).*"
    match_result = re.match(regex, version_desc)
    if match_result is None:
        raise Exception("Version tag not parsable")
    return match_result.group("tag")

class System(Enum):
    WINDOWS = "win32"
    LINUX = "linux"
    MAC = "darwin"
    UNKNOWN = "unknown"

def decode_platform() -> System:
    platform: System = System.UNKNOWN
    if sys.platform == System.WINDOWS.value:
        platform = System.WINDOWS
    elif sys.platform == System.LINUX.value:
        platform = System.LINUX
    elif sys.platform == System.MAC.value:
        platform = System.MAC
    return platform

def create_appdata_directory(system: System, dir_name: str) -> Path:
    match system:
        case System.LINUX:
            return Path.home() / ("." + dir_name)
        case System.WINDOWS:
            return Path(os.environ['APPDATA']) / dir_name
        case System.MAC:
            return Path("/Library/Application Support") / dir_name
    assert (False)



PLATFORM: Final[System] = decode_platform()
SOFTWARE_VERSION: Final[Version] = Version.to_version(get_version_tag())
APP_DATA_DIR: Final[Path] = create_appdata_directory(PLATFORM, "SonicControl")

ENCODING: Final[str] = "utf-8"

