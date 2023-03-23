import numpy as np
import cv2
import copy
import os
import sys
from PIL import Image
from pprint import pprint

# setting path
sys.path.append(os.path.dirname(os.path.dirname(os.getcwd())))

# import local modules
from camj.general.launch import energy_simulation

from examples.rhythmic_pixel_21.mapping import mapping_function
from examples.rhythmic_pixel_21.sw import sw_pipeline
from examples.rhythmic_pixel_21.hw import hw_config


def run_energy_simulation(hw_desc, mapping, sw_desc):

    total_energy, energy_breakdown = energy_simulation(
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc,
    )

    print("Total energy: ", total_energy)
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

