import math
import tkinter as tk

from ttkbootstrap.style import StyleBuilderTTK


LINUX_TK_SCALING_BASELINE = 1.33398982438864281
MACOS_TK_SCALING_BASELINE = 1.000492368291482
MIN_VALID_TK_SCALING = 0.25
_SCALE_GUARD_INSTALLED = False


def _clamp_scaled_size(size: int | float | list[int]) -> int | list[int]:
    if isinstance(size, list):
        return [max(1, int(value)) for value in size]
    return max(1, int(size))


def _install_ttkbootstrap_scale_guard() -> None:
    global _SCALE_GUARD_INSTALLED

    if _SCALE_GUARD_INSTALLED:
        return

    original_scale_size = StyleBuilderTTK.scale_size

    def guarded_scale_size(self, size):
        return _clamp_scaled_size(original_scale_size(self, size))

    StyleBuilderTTK.scale_size = guarded_scale_size
    _SCALE_GUARD_INSTALLED = True


def ensure_valid_tk_scaling(root: tk.Misc) -> None:
    _install_ttkbootstrap_scale_guard()

    winsys = root.tk.call("tk", "windowingsystem")
    scaling = root.tk.call("tk", "scaling")

    try:
        scaling_value = float(scaling)
    except (TypeError, ValueError):
        scaling_value = math.nan

    if math.isfinite(scaling_value) and scaling_value >= MIN_VALID_TK_SCALING:
        return

    baseline = MACOS_TK_SCALING_BASELINE if winsys == "aqua" else LINUX_TK_SCALING_BASELINE
    root.tk.call("tk", "scaling", baseline)