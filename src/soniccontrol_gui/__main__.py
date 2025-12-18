import asyncio
from soniccontrol_gui import start_gui
import os
from pathlib import Path

from soniccontrol_gui.plugins.device_plugin import register_device_plugins
from soniccontrol_gui.utils.widget_registry import WidgetRegistry

if __name__ == "__main__":
    register_device_plugins()

    in_dev_env = "FIRMWARE_BUILD_DIR_PATH" in os.environ
    simulation_exe_path = None
    if in_dev_env:
        # We could do this somehow else. But this is easy and simple
        WidgetRegistry.set_up()
        simulation_exe_path = Path(os.environ["FIRMWARE_BUILD_DIR_PATH"] + "/linux/platform_linux/src/device/device_main")

    start_gui(simulation_exe_path)
 
