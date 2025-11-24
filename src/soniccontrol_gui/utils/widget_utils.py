import ttkbootstrap as ttk
import tkinter as tk

def enable_all_children(widget: tk.Widget, enabled: bool):
    for child in widget.winfo_children():
        # Check here if the child has a state option for configure
        config_opts = child.configure()
        if config_opts and "state" in config_opts: 
            # widgets with the state option can be disabled. Frames do not have such an option
            child.configure(state=ttk.NORMAL if enabled else ttk.DISABLED) # type: ignore
        enable_all_children(child, enabled)

