import os
from pathlib import Path
import sys
from enum import Enum
from typing import Final


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
