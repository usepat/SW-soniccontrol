import os
from pathlib import Path

from soniccontrol.app_config import PLATFORM, System


def open_file_explorer(path: Path):
    os_native_path = str(path)
    if PLATFORM == System.WINDOWS:
        os.startfile(os_native_path) 
    elif PLATFORM == System.MAC:
        os.system(f"open {os_native_path!r}") # !r calls repr on string and ensures proper escaping of special characters
    elif PLATFORM == System.LINUX:
        os.system(f"xdg-open {os_native_path!r}")
    else:
        raise Exception("Unknown platform. Cannot open file explorer")