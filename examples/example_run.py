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


########################################################
#               Validation Examples                    # 
########################################################

# A 0.62mW Ultra-Low-Power Convolutional-NeuralNetwork Face-Recognition Processor 
# and a CIS Integrated with Always-On Haar-Like Face Detector
def run_isscc_17_0_62():

    from examples.isscc_17_0_62.mapping import mapping_function
    from examples.isscc_17_0_62.sw import sw_pipeline
    from examples.isscc_17_0_62.hw import hw_config
    
    hw_dict = hw_config()
    mapping_dict = mapping_function()
    sw_stage_list = sw_pipeline()

    run_energy_simulation(
        hw_dict = hw_dict,
        mapping_dict = mapping_dict,
        sw_stage_list = sw_stage_list
    )

# A Data-Compressive 1.5b/2.75b Log-Gradient QVGA Image Sensor with Multi-Scale Readout
# for Always-On Object Detection
def run_jssc_19():

    from examples.jssc_19.mapping import mapping_function
    from examples.jssc_19.sw import sw_pipeline
    from examples.jssc_19.hw import hw_config
    
    hw_dict = hw_config()
    mapping_dict = mapping_function()
    sw_stage_list = sw_pipeline()

    run_energy_simulation(
        hw_dict = hw_dict,
        mapping_dict = mapping_dict,
        sw_stage_list = sw_stage_list
    )

# Design of an Always-On Image Sensor Using an Analog Lightweight Convolutional Neural Network
def run_sensors_20():

    from examples.sensors_20.mapping import mapping_function
    from examples.sensors_20.sw import sw_pipeline
    from examples.sensors_20.hw import hw_config
    
    hw_dict = hw_config()
    mapping_dict = mapping_function()
    sw_stage_list = sw_pipeline()

    run_energy_simulation(
        hw_dict = hw_dict,
        mapping_dict = mapping_dict,
        sw_stage_list = sw_stage_list
    )

# A 1/2.3inch 12.3Mpixel with On-Chip 4.97TOPS/W CNN Processor Back-Illuminated Stacked CMOS Image Sensor
def run_isscc_21():
    
    from examples.isscc_21_back_illuminated.mapping import mapping_function
    from examples.isscc_21_back_illuminated.sw import sw_pipeline
    from examples.isscc_21_back_illuminated.hw import hw_config
    
    hw_dict = hw_config()
    mapping_dict = mapping_function()
    sw_stage_list = sw_pipeline()

    run_energy_simulation(
        hw_dict = hw_dict,
        mapping_dict = mapping_dict,
        sw_stage_list = sw_stage_list
    )

# A 0.5-V Real-Time Computational CMOS Image Sensor With Programmable Kernel for Feature Extraction
def run_jssc21_05v():

    from examples.jssc21_05v.mapping import mapping_function
    from examples.jssc21_05v.sw import sw_pipeline
    from examples.jssc21_05v.hw import hw_config
    
    hw_dict = hw_config()
    mapping_dict = mapping_function()
    sw_stage_list = sw_pipeline()

    run_energy_simulation(
        hw_dict = hw_dict,
        mapping_dict = mapping_dict,
        sw_stage_list = sw_stage_list
    )

# A 51-pJ/Pixel 33.7-dB PSNR 4× Compressive CMOS Image Sensor With 
# Column-Parallel Single-Shot Compressive Sensing
def run_jssc21_51pj():

    from examples.jssc21_51pj.mapping import mapping_function
    from examples.jssc21_51pj.sw import sw_pipeline
    from examples.jssc21_51pj.hw import hw_config
    
    hw_dict = hw_config()
    mapping_dict = mapping_function()
    sw_stage_list = sw_pipeline()

    run_energy_simulation(
        hw_dict = hw_dict,
        mapping_dict = mapping_dict,
        sw_stage_list = sw_stage_list
    )

# A 2.6 e-rms Low-Random-Noise, 116.2 mW Low-Power 2-Mp Global Shutter 
# CMOS Image Sensor with Pixel-Level ADC and In-Pixel Memory
def run_vlsi_21():

    from examples.vlsi_21.mapping import mapping_function
    from examples.vlsi_21.sw import sw_pipeline
    from examples.vlsi_21.hw import hw_config
    
    hw_dict = hw_config()
    mapping_dict = mapping_function()
    sw_stage_list = sw_pipeline()

    run_energy_simulation(
        hw_dict = hw_dict,
        mapping_dict = mapping_dict,
        sw_stage_list = sw_stage_list
    )

# A 0.8V Intelligent Vision Sensor with Tiny Convolutional Neural Network and 
# Programmable Weights Using Mixed-Mode Processing-in-Sensor Technique for Image Classification 
def run_isscc_22_08v():

    from examples.isscc_22_08v.mapping import mapping_function
    from examples.isscc_22_08v.sw import sw_pipeline
    from examples.isscc_22_08v.hw import hw_config
    
    hw_dict = hw_config()
    mapping_dict = mapping_function()
    sw_stage_list = sw_pipeline()

    run_energy_simulation(
        hw_dict = hw_dict,
        mapping_dict = mapping_dict,
        sw_stage_list = sw_stage_list
    )

# Senputing: An Ultra-Low-Power Always-On Vision Perception Chip
# Featuring the Deep Fusion of Sensing and Computing
def run_tcas_i22():

    from examples.tcas_i22.mapping import mapping_function
    from examples.tcas_i22.sw import sw_pipeline
    from examples.tcas_i22.hw import hw_config
    
    hw_dict = hw_config()
    mapping_dict = mapping_function()
    sw_stage_list = sw_pipeline()

    run_energy_simulation(
        hw_dict = hw_dict,
        mapping_dict = mapping_dict,
        sw_stage_list = sw_stage_list
    )

########################################################
#               Evaluation Examples                    # 
########################################################

def run_ieee_vr22():

    from examples.ieee_vr22.mapping import mapping_function_w_analog
    from examples.ieee_vr22.sw import sw_pipeline_w_analog
    from examples.ieee_vr22.hw import hw_config_w_analog

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
    
    run_energy_simulation(
        hw_dict = hw_dict,
        mapping_dict = mapping_dict,
        sw_stage_list = sw_stage_list
    )


if __name__ == '__main__':

    args = options()

    # Validation
    if args.isscc_17_0_62:
        run_isscc_17_0_62()
    if args.jssc_19:
        run_jssc_19()
    if args.sensors_20:
        run_sensors_20()
    if args.isscc_21:
        run_isscc_21()
    if args.jssc21_05v:
        run_jssc21_05v()
    if args.jssc21_51pj:
        run_jssc21_51pj()
    if args.vlsi_21:
        run_vlsi_21()    
    if args.isscc_22_08v:
        run_isscc_22_08v()
    if args.tcas_i22:
        run_tcas_i22()
    
    # Evaluation
    if args.ieee_vr22:
        run_ieee_vr22()

