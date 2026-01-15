

from enum import IntEnum


class DeviceState(IntEnum):
    OFF = 0 # deprecated
    BROKEN = 1 # deprecated
    READY = 2 
    SERVICE = 3
    WAKE_UP = 4
    EXIT_APP = 5 # deprecated