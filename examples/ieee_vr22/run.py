from pprint import pprint
import numpy as np
from PIL import Image
import copy
import os
import sys

# setting path
sys.path.append(os.path.dirname(os.path.dirname(os.getcwd())))

# import local modules
from camj.general.launch import energy_simulation, functional_simulation

from examples.ieee_vr22.mapping import mapping_function, mapping_function_w_analog
from examples.ieee_vr22.sw import sw_pipeline, sw_pipeline_w_analog
from examples.ieee_vr22.hw import hw_config, hw_config_w_analog

def eventification_noise_simulation_example(
    prev_img_name,
    curr_img_name,
    hw_desc,
    mapping,
    sw_desc
):

    # sensor specs
    full_scale_input_voltage = 1.8 # V
    pixel_full_well_capacity = 10000 # e

    # load test image
    curr_img = np.array(Image.open(curr_img_name).convert("L"))

    # a simple inverse img to photon
    electron_input = np.expand_dims(curr_img / 255 * pixel_full_well_capacity, axis = 2)

    prev_img = np.array(Image.open(prev_img_name).convert("L"))
    prev_img = np.expand_dims(prev_img / 255. * full_scale_input_voltage, axis = 2)

    input_mapping = {
        "CurrInput" : [electron_input],
        "PrevResizedInput" : [prev_img]
    }

    simulation_res = functional_simulation(
        sw_desc, 
        hw_desc, 
        mapping, 
        input_mapping
    )

    img_after_adc = simulation_res['Eventification'][0]
    img_res = Image.fromarray(np.uint8(np.squeeze(img_after_adc) * 255) , 'L')
    img_res.show()

def run_energy_simulation(hw_desc, mapping, sw_desc):

    total_energy, energy_breakdown = energy_simulation(
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )

    print("Total energy: ", total_energy)
    print("Energy breakdown:")
    pprint(energy_breakdown)

if __name__ == '__main__':
    
    hw_desc = hw_config_w_analog()
    mapping = mapping_function_w_analog()
    sw_desc = sw_pipeline_w_analog()


    # uncomment these to simulate the eventification in digital domain,
    # HOWEVER, this cannot operate noise simulation!
    # hw_desc = hw_config()
    # mapping = mapping_function()
    # sw_desc = sw_pipeline()

    # eventification simulation
    eventification_noise_simulation_example(
        prev_img_name = "../../test_imgs/test_eye1.png",
        curr_img_name = "../../test_imgs/test_eye2.png",
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )
    
    run_energy_simulation(
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )
