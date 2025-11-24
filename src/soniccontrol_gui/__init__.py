from __future__ import annotations
import asyncio

from PIL import Image

from soniccontrol_gui.widgets.message_box import MessageBox
Image.CUBIC = Image.BICUBIC # FIX: because ttk.bootstrap sets an deprecated, removed value

import fnmatch
import json
import logging
import logging.config
import pathlib
import subprocess
import sys
import os
from typing import Optional
from ttkbootstrap.utility import enable_high_dpi_awareness
from async_tkinter_loop import async_mainloop
from soniccontrol_gui.views.core.connection_window import ConnectionWindow
from soniccontrol.app_config import System, PLATFORM
from soniccontrol_gui.constants import files
from soniccontrol_gui.resources import resources
from importlib import resources as rs

# create directories if missing
os.makedirs(files.DATA_DIR, exist_ok=True)
os.makedirs(files.LOG_DIR, exist_ok=True)
os.makedirs(files.MEASUREMENTS_DIR, exist_ok=True)

def setup_logging() -> None:
    config_file: pathlib.Path = resources.LOGGING_CONFIG
    with config_file.open() as file:
        config = json.load(file)
    logging.config.dictConfig(config)

setup_logging()
soniccontrol_logger: logging.Logger = logging.getLogger("soniccontrol")

def check_high_dpi_windows() -> None:
    if PLATFORM == System.WINDOWS:
        enable_high_dpi_awareness()


def setup_fonts() -> None:
    soniccontrol_logger.info("Installing fonts...")
    font_files = []
    for font_resource in resources.FONTS.iterdir():
        if fnmatch.fnmatch(font_resource.name, "*.ttf"):
            font_files.append(str(font_resource))
    try:
        process = subprocess.run(
            [
                str(rs.files(f"soniccontrol_gui.bin.font-install.{sys.platform}").joinpath("font-install")),
                *list(font for font in font_files),
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL # Devnull, so that they do not print to the command line
        )
        if process.returncode != 0:
            raise RuntimeError("Failed to install fonts")
    except Exception:
        soniccontrol_logger.warning("Failed to install fonts", exc_info=True)


check_high_dpi_windows()
setup_fonts()



def start_gui(simulation_exe_path: Optional[pathlib.Path] = None):
    main_window = ConnectionWindow(simulation_exe_path=simulation_exe_path)
    root = main_window.view

    if PLATFORM != System.WINDOWS:
        soniccontrol_logger.info("Enabling high dpi awareness for DARWIN/ LINUX")
        enable_high_dpi_awareness(root)    

    def global_exception_handler(loop, context):
        soniccontrol_logger.error(context['message'])
        exception = context.get("exception")
        if exception:
            soniccontrol_logger.error(str(exception))
            MessageBox.show_error(root, str(exception))
    
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(global_exception_handler)
    asyncio.set_event_loop(loop)

    async_mainloop(root)

soniccontrol_logger.info("Python: %s", sys.version)
soniccontrol_logger.info("Platform: %s", sys.platform)
