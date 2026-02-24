
from importlib import metadata
import sys
from typing import Any, List

from soniccontrol_gui.constants import _Files


def discover_plugins(group: str) -> List[Any]:
    plugins = []

    # 1) Built-in / bundled / normally installed entry points
    try:
        for ep in metadata.entry_points().select(group=group):
            plugins.append(ep.load())
    except Exception:
        # Don't let a broken plugin kill startup
        pass

    # 2) Plugins dropped into ./plugins (wheels unzipped here)
    _Files.PLUGINS.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(_Files.PLUGINS))  # allow importing plugin packages

    for dist in metadata.distributions(path=[str(_Files.PLUGINS)]):
        for ep in dist.entry_points:
            if ep.group == group:
                try:
                    plugins.append(ep.load())
                except Exception as e:
                    # log it; ignore bad plugin
                    print(f"Expection: {e}")
                    pass

    return plugins
