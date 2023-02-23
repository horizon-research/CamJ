import os
import sys
# directory reach
directory = os.getcwd()
parent_directory = os.path.dirname(directory)
# setting path
sys.path.append(os.path.dirname(directory))
sys.path.append(os.path.dirname(parent_directory))

from examples.jssc21_05v.analog_config import analog_config

# an example of user defined hw configuration setup 
def hw_config():

	hw_dict = {
		"memory": [],
		"compute": [],
        "analog": analog_config()
	}

	return hw_dict
