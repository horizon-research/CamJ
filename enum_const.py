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
	ANALOG = 1
	DIGITAL = 2

class Padding(Enum):
	NONE = 0
	ZEROS = 1