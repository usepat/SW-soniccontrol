

from enum import IntEnum


class DeviceState(IntEnum):
    OFF = 0
    BROKEN = 1
    READY = 2
    SERVICE = 3
    WAKE_UP = 4
    EXIT_APP = 5