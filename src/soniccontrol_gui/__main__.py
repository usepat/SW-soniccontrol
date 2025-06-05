from soniccontrol_gui import start_gui
import os
from pathlib import Path

from soniccontrol_gui.utils.widget_registry import WidgetRegistry

if __name__ == "__main__":
    simulation_exe_path = None
    if "SIMULATION_EXE_PATH" in os.environ:
        simulation_exe_path = Path(os.environ["SIMULATION_EXE_PATH"])

        # We could do this somehow else. But this is easy and simple
        WidgetRegistry.set_up()

    start_gui(simulation_exe_path)
