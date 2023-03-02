from pprint import pprint
import numpy as np
from PIL import Image
import copy
import os
import sys

# setting path
sys.path.append(os.path.dirname(os.path.dirname(os.getcwd())))

# import local modules
from camj.sim_core.launch import launch_simulation
from camj.functional_core.launch import launch_functional_simulation

# from examples.ieee_vr22.mapping import mapping_function, mapping_function_w_analog
# from examples.ieee_vr22.sw import sw_pipeline, sw_pipeline_w_analog
# from examples.ieee_vr22.hw import hw_config, hw_config_w_analog

from examples.ieee_vr22.mapping import mapping_function
from examples.ieee_vr22.sw import sw_pipeline
from examples.ieee_vr22.hw import hw_config

def eventification_noise_simulation_example(
    prev_img_name,
    curr_img_name,
    hw_dict,
    mapping_dict,
    sw_stage_list
):

    # sensor specs
    full_scale_input_voltage = 1.8 # V
    pixel_full_well_capacity = 10000 # e

    # load test image
    curr_img = np.array(Image.open(curr_img_name).convert("L"))

    # a simple inverse img to photon
    photon_input = curr_img/255.*pixel_full_well_capacity

    prev_img = np.array(Image.open(prev_img_name).convert("L"))/255.*full_scale_input_voltage

    input_mapping = {
        "CurrInput" : [photon_input],
        "PrevResizedInput" : [prev_img]
    }

    simulation_res = launch_functional_simulation(
        sw_stage_list, 
        hw_dict, 
        mapping_dict, 
        input_mapping
    )

    img_after_adc = simulation_res['Eventification'][0]
    img_res = Image.fromarray(np.uint8(img_after_adc * 255) , 'L')
    img_res.save("tmp.png")

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
    
    # hw_dict = hw_config_w_analog()
    # mapping_dict = mapping_function_w_analog()
    # sw_stage_list = sw_pipeline_w_analog()


    # uncomment these to simulate the eventification in digital domain,
    # HOWEVER, this cannot operate noise simulation!
    hw_dict = hw_config()
    mapping_dict = mapping_function()
    sw_stage_list = sw_pipeline()

    # eventification simulation
    # eventification_noise_simulation_example(
    #     prev_img_name = "../../test_imgs/test_eye1.png",
    #     curr_img_name = "../../test_imgs/test_eye2.png",
    #     hw_dict = hw_dict,
    #     mapping_dict = mapping_dict,
    #     sw_stage_list = sw_stage_list
    # )
    
    run_energy_simulation(
        hw_dict = hw_dict,
        mapping_dict = mapping_dict,
        sw_stage_list = sw_stage_list
    )
