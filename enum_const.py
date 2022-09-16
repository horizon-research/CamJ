from enum import Enum

class ProcessorLocation(Enum):
	SENSOR_LAYER = 1
	COMPUTE_LAYER = 2
	OFF_CHIP = 3

class ProcessDomain(Enum):
	ANALOG = 1
	DIGITAL = 2