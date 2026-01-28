

from enum import IntEnum

class TestInteraction(IntEnum):
    VALIDATION = 0
    PHYSICAL_INTERACTION = 1

class TestResult(IntEnum):
    SUCCESS = 0
    FAILURE = 1
    SEMI_AUTOMATED_STEP = 2
