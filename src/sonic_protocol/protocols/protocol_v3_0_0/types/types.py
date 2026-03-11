

from enum import IntEnum

class TestInteraction(IntEnum):
    VALIDATION = 0
    PHYSICAL_INTERACTION = 1

class TestResult(IntEnum):
    SUCCESS = 0
    FAILURE = 1
    SEMI_AUTOMATED_STEP = 2
    COMPLETED = 3

class UartInterface(IntEnum):
    RS232 = 0
    RS485 = 0

class Parity(IntEnum):
    EVEN = 0
    ODD = 1
    NO = 2
