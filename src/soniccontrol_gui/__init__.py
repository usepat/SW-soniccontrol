from __future__ import annotations
import asyncio
import traceback

from PIL import Image

from soniccontrol_gui.plugins.ui_plugin import register_ui_plugins
from soniccontrol_gui.widgets.message_box import MessageBox
Image.CUBIC = Image.BICUBIC # FIX: because ttk.bootstrap sets an deprecated, removed value

import fnmatch
import json
import logging
import logging.config
import pathlib
from pathlib import Path
import subprocess
import sys
import os
import click
from typing import Optional
from ttkbootstrap.utility import enable_high_dpi_awareness
from async_tkinter_loop import async_mainloop
from soniccontrol_gui.views.core.connection_window import ConnectionWindow
from soniccontrol.app_config import APP_CONFIG, AppConfig, System, PLATFORM, get_simulation_exe
from soniccontrol_gui.constants import files
from soniccontrol_gui.resources import resources
from importlib import resources as rs
from soniccontrol_gui.plugins.device_plugin import register_device_plugins
from soniccontrol_gui.utils.widget_registry import WidgetRegistry

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


@click.command()
@click.option("--remote-server-url", default=None)
def start_gui(remote_server_url: str | None):
    # change global variable.
    # We use a global variable here, because it is 
    # very tedious to propagate a single variable through 10 functions
    APP_CONFIG.remote_server_url = remote_server_url

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    register_device_plugins()
    register_ui_plugins()

    in_dev_env = "FIRMWARE_BUILD_DIR_PATH" in os.environ
    if in_dev_env:
        # We could do this somehow else. But this is easy and simple
        WidgetRegistry.set_up(loop)

    main_window = ConnectionWindow(
        simulation_exe_path=get_simulation_exe()
    )
    root = main_window.view

    if PLATFORM != System.WINDOWS:
        soniccontrol_logger.info("Enabling high dpi awareness for DARWIN/ LINUX")
        enable_high_dpi_awareness(root)    

    def global_exception_handler(loop, context):
        soniccontrol_logger.error(context['message'])
        exception = context.get("exception")
        if exception:
            error_str = "".join(traceback.format_exception(exception, limit=10))
            soniccontrol_logger.error(error_str)
            try:
                if root.winfo_exists():
                    MessageBox.show_error(root, error_str)
            except Exception:
                soniccontrol_logger.warning("Could not show error dialog during shutdown")
    
    loop.set_exception_handler(global_exception_handler)
    asyncio.set_event_loop(loop)

    async_mainloop(root)

soniccontrol_logger.info("Python: %s", sys.version)
soniccontrol_logger.info("Platform: %s", sys.platform)
