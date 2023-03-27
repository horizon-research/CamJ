from pprint import pprint
import numpy as np
from PIL import Image
import copy
import os
import sys

# setting path
sys.path.append(os.path.dirname(os.getcwd()))

# import local modules
from camj.general.launch import energy_simulation, functional_simulation

from examples.opt import options

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


########################################################
#               Validation Examples                    # 
########################################################

# A 0.62mW Ultra-Low-Power Convolutional-NeuralNetwork Face-Recognition Processor 
# and a CIS Integrated with Always-On Haar-Like Face Detector
def run_isscc_17_0_62():

    from examples.isscc_17_0_62.mapping import mapping_function
    from examples.isscc_17_0_62.sw import sw_pipeline
    from examples.isscc_17_0_62.hw import hw_config
    
    hw_desc = hw_config()
    mapping = mapping_function()
    sw_desc = sw_pipeline()

    run_energy_simulation(
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )

# A Data-Compressive 1.5b/2.75b Log-Gradient QVGA Image Sensor with Multi-Scale Readout
# for Always-On Object Detection
def run_jssc_19():

    from examples.jssc_19.mapping import mapping_function
    from examples.jssc_19.sw import sw_pipeline
    from examples.jssc_19.hw import hw_config
    
    hw_desc = hw_config()
    mapping = mapping_function()
    sw_desc = sw_pipeline()

    run_energy_simulation(
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )

# Design of an Always-On Image Sensor Using an Analog Lightweight Convolutional Neural Network
def run_sensors_20():

    from examples.sensors_20.mapping import mapping_function
    from examples.sensors_20.sw import sw_pipeline
    from examples.sensors_20.hw import hw_config
    
    hw_desc = hw_config()
    mapping = mapping_function()
    sw_desc = sw_pipeline()

    run_energy_simulation(
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )

# A 1/2.3inch 12.3Mpixel with On-Chip 4.97TOPS/W CNN Processor Back-Illuminated Stacked CMOS Image Sensor
def run_isscc_21():
    
    from examples.isscc_21_back_illuminated.mapping import mapping_function
    from examples.isscc_21_back_illuminated.sw import sw_pipeline
    from examples.isscc_21_back_illuminated.hw import hw_config
    
    hw_desc = hw_config()
    mapping = mapping_function()
    sw_desc = sw_pipeline()

    run_energy_simulation(
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )

# A 0.5-V Real-Time Computational CMOS Image Sensor With Programmable Kernel for Feature Extraction
def run_jssc21_05v():

    from examples.jssc21_05v.mapping import mapping_function
    from examples.jssc21_05v.sw import sw_pipeline
    from examples.jssc21_05v.hw import hw_config
    
    hw_desc = hw_config()
    mapping = mapping_function()
    sw_desc = sw_pipeline()

    run_energy_simulation(
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )

# A 51-pJ/Pixel 33.7-dB PSNR 4× Compressive CMOS Image Sensor With 
# Column-Parallel Single-Shot Compressive Sensing
def run_jssc21_51pj():

    from examples.jssc21_51pj.mapping import mapping_function
    from examples.jssc21_51pj.sw import sw_pipeline
    from examples.jssc21_51pj.hw import hw_config
    
    hw_desc = hw_config()
    mapping = mapping_function()
    sw_desc = sw_pipeline()

    run_energy_simulation(
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )

# A 2.6 e-rms Low-Random-Noise, 116.2 mW Low-Power 2-Mp Global Shutter 
# CMOS Image Sensor with Pixel-Level ADC and In-Pixel Memory
def run_vlsi_21():

    from examples.vlsi_21.mapping import mapping_function
    from examples.vlsi_21.sw import sw_pipeline
    from examples.vlsi_21.hw import hw_config
    
    hw_desc = hw_config()
    mapping = mapping_function()
    sw_desc = sw_pipeline()

    run_energy_simulation(
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )

# A 0.8V Intelligent Vision Sensor with Tiny Convolutional Neural Network and 
# Programmable Weights Using Mixed-Mode Processing-in-Sensor Technique for Image Classification 
def run_isscc_22_08v():

    from examples.isscc_22_08v.mapping import mapping_function
    from examples.isscc_22_08v.sw import sw_pipeline
    from examples.isscc_22_08v.hw import hw_config
    
    hw_desc = hw_config()
    mapping = mapping_function()
    sw_desc = sw_pipeline()

    run_energy_simulation(
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )

# Senputing: An Ultra-Low-Power Always-On Vision Perception Chip
# Featuring the Deep Fusion of Sensing and Computing
def run_tcas_i22():

    from examples.tcas_i22.mapping import mapping_function
    from examples.tcas_i22.sw import sw_pipeline
    from examples.tcas_i22.hw import hw_config
    
    hw_desc = hw_config()
    mapping = mapping_function()
    sw_desc = sw_pipeline()

    run_energy_simulation(
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )

########################################################
#               Evaluation Examples                    # 
########################################################

# Real Time Gaze Tracking with Event Driven Eye Segmentation
def run_ieee_vr22():

    from examples.ieee_vr22.mapping import mapping_function_w_analog
    from examples.ieee_vr22.sw import sw_pipeline_w_analog
    from examples.ieee_vr22.hw import hw_config_w_analog

    hw_desc = hw_config_w_analog()
    mapping = mapping_function_w_analog()
    sw_desc = sw_pipeline_w_analog()

    # eventification simulation
    eventification_noise_simulation_example(
        prev_img_name = "../test_imgs/test_eye1.png",
        curr_img_name = "../test_imgs/test_eye2.png",
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )
    
    run_energy_simulation(
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
    )

# Rhythmic Pixel Regions: Multi-resolution Visual Sensing System
# towards High-Precision Visual Computing at Low Power
def run_rhythmic_pixel_21():

    from examples.rhythmic_pixel_21.mapping import mapping_function
    from examples.rhythmic_pixel_21.sw import sw_pipeline
    from examples.rhythmic_pixel_21.hw import hw_config
    
    hw_desc = hw_config()
    mapping = mapping_function()
    sw_desc = sw_pipeline()

    run_energy_simulation(
        hw_desc = hw_desc,
        mapping = mapping,
        sw_desc = sw_desc
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
    if args.rhythmic_pixel_21:
        run_rhythmic_pixel_21()

