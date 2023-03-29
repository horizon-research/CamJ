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
from camj.general.launch import energy_simulation, functional_simulation

# import customized modules
from examples.isscc_17_0_62.mapping import mapping_function
from examples.isscc_17_0_62.sw import sw_pipeline
from examples.isscc_17_0_62.hw import hw_config

def run_energy_simulation(hw_desc, mapping, sw_desc):

    total_energy, energy_breakdown = energy_simulation(
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )


def run_functional_simulation(hw_desc, mapping, sw_desc, test_img_name):

    img_input = np.expand_dims(np.array(Image.open(test_img_name).convert("L").resize((240, 320))), axis = 2)

    # hand-craft a (20x20x1) weight input
    weight_input = np.ones((20, 20, 1))

    input_mapping = {
        "AnalogInput" : [img_input],
        "Weight" : [weight_input],
    }

    simulation_res = functional_simulation(
        sw_desc = sw_desc,
        hw_desc = hw_desc,
        mapping = mapping,
        input_mapping = input_mapping
    )
    end_result = simulation_res["Comparator"][0][:, :, 0]
    res_img = Image.fromarray(np.uint8(end_result / np.max(end_result) * 255) , 'L')
    res_img.show()


if __name__ == '__main__':

    hw_desc = hw_config()
    mapping = mapping_function()
    sw_desc = sw_pipeline()

    # run_functional_simulation(
    #     hw_desc = hw_desc,
    #     mapping = mapping,
    #     sw_desc = sw_desc,
    #     test_img_name = "../../test_imgs/test_eye1.png",
    # )

    run_energy_simulation(
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )

    


