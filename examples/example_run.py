from pprint import pprint
import numpy as np
import cv2
import copy
import os
import sys

# setting path
sys.path.append(os.path.dirname(os.getcwd()))

# import local modules
from camj.sim_core.launch import launch_simulation
from camj.functional_core.launch import launch_functional_simulation

from examples.opt import options

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
    curr_img = np.array(cv2.imread(curr_img_name, cv2.IMREAD_GRAYSCALE))
    # a simple inverse img to photon
    photon_input = curr_img/255*pixel_full_well_capacity

    prev_img = np.array(cv2.imread(prev_img_name, cv2.IMREAD_GRAYSCALE))/255*full_scale_input_voltage

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

    cv2.imshow("image after adc", img_after_adc/np.max(img_after_adc))
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def run_ieee_vr22():

    from examples.ieee_vr22.mapping_file import mapping_function, mapping_function_w_analog
    from examples.ieee_vr22.sw_pipeline import sw_pipeline, sw_pipeline_w_analog
    from examples.ieee_vr22.hw_config import hw_config, hw_config_w_analog

    hw_dict = hw_config_w_analog()
    mapping_dict = mapping_function_w_analog()
    sw_stage_list = sw_pipeline_w_analog()

    # eventification simulation
    eventification_noise_simulation_example(
        prev_img_name = "../test_imgs/test_eye1.png",
        curr_img_name = "../test_imgs/test_eye2.png",
        hw_dict = hw_dict,
        mapping_dict = mapping_dict,
        sw_stage_list = sw_stage_list
    )
    
    launch_simulation(
        hw_dict = hw_dict,
        mapping_dict = mapping_dict,
        sw_stage_list = sw_stage_list
    )

def run_isscc_22_08v():

    from examples.isscc_22_08v.mapping_file import mapping_function
    from examples.isscc_22_08v.sw_pipeline import sw_pipeline
    from examples.isscc_22_08v.hw_config import hw_config
    
    hw_dict = hw_config()
    mapping_dict = mapping_function()
    sw_stage_list = sw_pipeline()

    launch_simulation(
        hw_dict = hw_dict,
        mapping_dict = mapping_dict,
        sw_stage_list = sw_stage_list
    )

def run_tcas_i22():

    from examples.tcas_i22.mapping_file import mapping_function
    from examples.tcas_i22.sw_pipeline import sw_pipeline
    from examples.tcas_i22.hw_config import hw_config
    
    hw_dict = hw_config()
    mapping_dict = mapping_function()
    sw_stage_list = sw_pipeline()

    launch_simulation(
        hw_dict = hw_dict,
        mapping_dict = mapping_dict,
        sw_stage_list = sw_stage_list
    )

def run_jssc21_05v():

    from examples.jssc21_05v.mapping_file import mapping_function
    from examples.jssc21_05v.sw_pipeline import sw_pipeline
    from examples.jssc21_05v.hw_config import hw_config
    
    hw_dict = hw_config()
    mapping_dict = mapping_function()
    sw_stage_list = sw_pipeline()

    launch_simulation(
        hw_dict = hw_dict,
        mapping_dict = mapping_dict,
        sw_stage_list = sw_stage_list
    )

if __name__ == '__main__':

    args = options()

    if args.ieee_vr22:
        run_ieee_vr22()
    if args.isscc_22_08v:
        run_isscc_22_08v()
    if args.tcas_i22:
        run_tcas_i22()
    if args.jssc21_05v:
        run_jssc21_05v()





