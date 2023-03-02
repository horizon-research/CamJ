import numpy as np
import cv2
import copy
import os
import sys
from pprint import pprint

# setting path
sys.path.append(os.path.dirname(os.path.dirname(os.getcwd())))

# import local modules
from camj.sim_core.launch import launch_simulation

from examples.isscc_17_0_62.mapping import mapping_function
from examples.isscc_17_0_62.sw import sw_pipeline
from examples.isscc_17_0_62.hw import hw_config

def run_energy_simulation(hw_dict, mapping_dict, sw_stage_list):

    total_energy, energy_breakdown = launch_simulation(
        hw_dict = hw_dict,
        mapping_dict = mapping_dict,
        sw_stage_list = sw_stage_list
    )

    print("Total energy: ", total_energy)
    print("Energy breakdown:")
    pprint(energy_breakdown)


if __name__ == '__main__':

    hw_dict = hw_config()
    mapping_dict = mapping_function()
    sw_stage_list = sw_pipeline()

    run_energy_simulation(
        hw_dict = hw_dict,
        mapping_dict = mapping_dict,
        sw_stage_list = sw_stage_list
    )

