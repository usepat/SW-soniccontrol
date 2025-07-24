import asyncio
from soniccontrol_gui import start_gui
import os
from pathlib import Path

from soniccontrol_gui.plugins.device_plugin import register_device_plugins
from soniccontrol_gui.utils.widget_registry import WidgetRegistry

if __name__ == "__main__":
    register_device_plugins()

    in_dev_env = False
    simulation_exe_path = None
    if "FIRMWARE_BUILD_DIR_PATH" in os.environ:
        in_dev_env= True
        simulation_exe_path = Path(os.environ["FIRMWARE_BUILD_DIR_PATH"] + "/linux/mvp_simulation/src/simulation/cli_simulation_mvp/cli_simulation_mvp")

        # We could do this somehow else. But this is easy and simple
        WidgetRegistry.set_up()

    start_gui(simulation_exe_path)

    if in_dev_env:
        asyncio.run(WidgetRegistry.clean_up())
