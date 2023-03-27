import numpy as np
import cv2
import copy
import os
import sys
from pprint import pprint

# setting path
sys.path.append(os.path.dirname(os.path.dirname(os.getcwd())))

# import local modules
from camj.general.launch import energy_simulation

from examples.isscc_21_back_illuminated.mapping import mapping_function
from examples.isscc_21_back_illuminated.sw import sw_pipeline
from examples.isscc_21_back_illuminated.hw import hw_config

def run_energy_simulation(hw_desc, mapping, sw_desc):

    total_energy, energy_breakdown = energy_simulation(
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )


if __name__ == '__main__':

    hw_desc = hw_config()
    mapping = mapping_function()
    sw_desc = sw_pipeline()

    run_energy_simulation(
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )


