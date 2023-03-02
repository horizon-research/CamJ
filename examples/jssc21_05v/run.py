from pprint import pprint
import numpy as np
import cv2
import copy
import os
import sys

# setting path
sys.path.append(os.path.dirname(os.path.dirname(os.getcwd())))

# import local modules
from camj.sim_core.launch import launch_simulation

from examples.jssc21_05v.mapping import mapping_function
from examples.jssc21_05v.sw import sw_pipeline
from examples.jssc21_05v.hw import hw_config

def run_energy_simulation(hw_dict, mapping_dict, sw_stage_list):

    total_energy, energy_breakdown = launch_simulation(
        hw_dict = hw_dict,
        mapping_dict = mapping_dict,
        sw_stage_list = sw_stage_list
    )

    print("Total energy: ", total_energy, "pJ")
    print("Energy breakdown (pJ):")
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
