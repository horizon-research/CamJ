'''
    This file documents the global configuration enums.
'''

from enum import Enum

class ProcessorLocation(Enum):
    INVALID = 0
    SENSOR_LAYER = 1
    COMPUTE_LAYER = 2
    OFF_CHIP = 3

class ProcessDomain(Enum):
    DIGITAL = 1
    CURRENT = 2
    VOLTAGE = 3
    CHARGE = 4
    TIME = 5
    OPTICAL = 6
