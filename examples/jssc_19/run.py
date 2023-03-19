from pprint import pprint
import numpy as np
import cv2
import copy
import os
import sys

# setting path
sys.path.append(os.path.dirname(os.path.dirname(os.getcwd())))

# import local modules
from camj.general.launch import launch_simulation

# import customized modules
from examples.jssc_19.mapping import mapping_function
from examples.jssc_19.sw import sw_pipeline
from examples.jssc_19.hw import hw_config

def run_energy_simulation(hw_desc, mapping, sw_desc):

    total_energy, energy_breakdown = launch_simulation(
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )

    print("Total energy: ", total_energy, "pJ")
    print("Energy breakdown (pJ):")
    pprint(energy_breakdown)

if __name__ == '__main__':

    hw_desc = hw_config()
    mapping = mapping_function()
    sw_desc = sw_pipeline()

    run_energy_simulation(
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )
