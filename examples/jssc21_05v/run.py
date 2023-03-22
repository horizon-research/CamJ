from pprint import pprint
import numpy as np
import cv2
import copy
import os
import sys
from PIL import Image

# setting path
sys.path.append(os.path.dirname(os.path.dirname(os.getcwd())))

# import local modules
from camj.general.launch import energy_simulation, functional_simulation

from examples.jssc21_05v.mapping import mapping_function
from examples.jssc21_05v.sw import sw_pipeline
from examples.jssc21_05v.hw import hw_config

def run_energy_simulation(hw_desc, mapping, sw_desc):

    total_energy, energy_breakdown = energy_simulation(
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )

    print("Total energy: ", total_energy, "pJ")
    print("Energy breakdown (pJ):")
    pprint(energy_breakdown)

def run_functional_simulation(hw_desc, mapping, sw_desc, test_img_name):

    img_input = np.array(Image.open(test_img_name).convert("L"))

    # hand-craft a (3x3x8) weight input
    weight_input = np.zeros((3, 3, 1))
    # blurring and dimming
    weight_input[:, :, 0] = [
        [-1/3, -1/3, -1/3],
        [0, 0, 0],
        [1/3, 1/3, 1/3],
    ]

    input_mapping = {
        "Input" : [img_input],
        "Weight" : [weight_input],
    }

    simulation_res = functional_simulation(
        sw_desc = sw_desc,
        hw_desc = hw_desc,
        mapping = mapping,
        input_mapping = input_mapping
    )
    res_img = Image.fromarray(np.uint8(simulation_res["Time2VoltageConv"][0][:, :, 0]) , 'L')
    res_img.show()

if __name__ == '__main__':

    hw_desc = hw_config()
    mapping = mapping_function()
    sw_desc = sw_pipeline()

    run_energy_simulation(
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )

    run_functional_simulation(
        hw_desc = hw_desc, 
        mapping = mapping, 
        sw_desc = sw_desc, 
        test_img_name = "../../test_imgs/test_eye1.png",
    )
