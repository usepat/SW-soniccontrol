import os
import sys
import tkinter as tk

# I had a bug when using RDP where the GUI would be really slow during startup and this fixed it.
# But for some reason I could not replicate the bug and so I will keep this here to remember the "fix"
# and investigate it later

# Disabling useinputmethods for some reason fixes a bug where using the home spinbox the first times pauses the GUI for a few seconds


TK_USE_INPUT_METHODS_ENV = "SONICCONTROL_TK_USE_INPUT_METHODS"


def configure_tk_input_methods(window: tk.Misc) -> None:
    """Avoid synchronous XIM setup on Linux X11 before windows receive focus.

    An unresponsive input-method server can block XCreateIC for seconds inside
    Tk event processing, freezing both the GUI and asyncio. Standard keyboard
    input still works without XIM; users needing an IME can opt in explicitly.
    """
    if not sys.platform.startswith("linux"):
        return
    if os.environ.get(TK_USE_INPUT_METHODS_ENV) == "1":
        return
    if window.tk.call("tk", "windowingsystem") == "x11":
        window.tk.call("tk", "useinputmethods", False)