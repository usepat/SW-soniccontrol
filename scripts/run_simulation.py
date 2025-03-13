import asyncio
from pathlib import Path
from soniccontrol_gui import start_gui
import os

from soniccontrol_gui.utils.widget_registry import WidgetRegistry

if __name__ == "__main__":
    WidgetRegistry.set_up()
    simulation_exe_path = Path(os.environ["SIMULATION_EXE_PATH"])
    simulation_exe_path = Path("/home/usepat/GitHub/FW-sonic-firmware/build/linux/mvp_simulation_descale/test/cli/cli_simulation_descale/cli_simulation_descale")
    start_gui(simulation_exe_path)
    asyncio.run(WidgetRegistry.clean_up())
