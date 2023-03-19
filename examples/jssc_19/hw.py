import os
import sys
# directory reach
parent_directory = os.path.dirname(os.getcwd())
# setting path
sys.path.append(os.path.dirname(parent_directory))

# import local modules
from camj.digital.compute import ADC, ComputeUnit
from camj.digital.memory import FIFO, LineBuffer
from camj.general.enum import ProcessorLocation, ProcessDomain

# import customized modules
from examples.jssc_19.analog import analog_config

# an example of user defined hw configuration setup 
def hw_config():

    hw_dict = {
        "memory": [],
        "compute": [],
        "analog": analog_config()
    }

    return hw_dict
