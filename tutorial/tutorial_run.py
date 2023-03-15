from pprint import pprint
import numpy as np
from PIL import Image
import copy
import os
import sys

# setting path
sys.path.append(os.path.dirname(os.getcwd()))

# import local modules
from camj.sim_core.launch import launch_simulation
from camj.functional_core.launch import launch_functional_simulation

# import tutorial example configuration modules
from tutorial.mapping import mapping_function
from tutorial.sw import sw_pipeline
from tutorial.hw import hw_config

# functional simulation harness function
def tutorial_functional_simulation(
    img_name,
    hw_desc,
    mapping,
    sw_desc
):

    # sensor specs
    full_scale_input_voltage = 1.8 # V
    pixel_full_well_capacity = 10000 # e

    # load test image
    img = np.array(Image.open(img_name).convert("L"))
    # a simple inverse img to electrons and converts to a 3-dimensional matrix
    electron_input = np.expand_dims(img/255*pixel_full_well_capacity, axis=2)

    input_mapping = {
        "Input" : [electron_input]
    }

    simulation_res = launch_functional_simulation(sw_desc, hw_desc, mapping, input_mapping)

    img_after_adc = simulation_res["AnalogToDigitalConverter"][0]
    img_res = Image.fromarray(np.uint8(np.squeeze(img_after_adc)) , 'L')
    img_res.show()

    hw_desc["analog"][0].components[1].component_list[0][0].noise_model.noise = 0.5

    simulation_res = launch_functional_simulation(sw_desc, hw_desc, mapping, input_mapping)

    img_after_adc = simulation_res["AnalogToDigitalConverter"][0]
    img_res = Image.fromarray(np.uint8(np.squeeze(img_after_adc)) , 'L')
    img_res.show()


def main():

    hw_desc = hw_config()
    mapping = mapping_function()
    sw_desc = sw_pipeline()

    tutorial_functional_simulation(
        img_name = "../test_imgs/test_img2.jpeg",
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )
    
    launch_simulation(
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )

if __name__ == '__main__':
    main()
