import os

from soniccontrol_gui import start_gui


os.environ.setdefault("SONICCONTROL_CONNECTION_MODES", "default,legacy_crystal")


if __name__ == "__main__":
    start_gui()