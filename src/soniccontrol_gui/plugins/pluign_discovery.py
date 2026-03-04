
from importlib import metadata
import sys
import os
from typing import Any, List

from soniccontrol_gui.constants import _Files


def discover_plugins(group: str) -> List[Any]:
    plugins = []

    # 1) normally installed entry points 
    # Do get added by installing a library over pip into the venv
    try:
        for ep in metadata.entry_points().select(group=group):
            plugins.append(ep.load())
    except Exception:
        # Don't let a broken plugin kill startup
        pass

    # 2) Plugins dropped into ./plugins (wheels unzipped here)
    plugin_dirs=[str(_Files.PLUGINS)]
    _Files.PLUGINS.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(_Files.PLUGINS))  # allow importing plugin packages from the directory

    # 3) In a bundled application all dependencies and packages are inside _internal folder
    # When using pyinstaller with --one-directory option
    is_bundled_application = getattr(sys, "frozen", False)
    if is_bundled_application:
        # PyInstaller sets _MEIPASS to the _internal folder, where all collected packagers lay.
        bundled_dependencies_dir: Path = sys._MEIPASS # type: ignore
        plugin_dirs.append(bundled_dependencies_dir)

    for dist in metadata.distributions(path=plugin_dirs):
        for ep in dist.entry_points:
            if ep.group == group:
                try:
                    plugins.append(ep.load())
                except Exception as e:
                    # log it; ignore bad plugin
                    print(f"Expection: {e}")
                    pass

    return plugins
