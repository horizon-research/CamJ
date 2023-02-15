import os
import sys
# directory reach
directory = os.getcwd()
parent_directory = os.path.dirname(directory)
# setting path
sys.path.append(os.path.dirname(directory))
sys.path.append(os.path.dirname(parent_directory))

import cv2
import numpy as np

from sim_core.pixel_libs import ActivePixelSensor, DigitalPixelSensor, PulseWidthModulationPixel

def test_3t_aps(img_name):
    img = np.array(cv2.imread(img_name, cv2.IMREAD_GRAYSCALE))
    # sensor specs
    full_scale_input_voltage = 1.8 # V
    pixel_full_well_capacity = 10000 # e
    conversion_gain = full_scale_input_voltage/pixel_full_well_capacity

    photon_input = img/255*pixel_full_well_capacity

    aps_3t = ActivePixelSensor(
        # performance parameters
        pd_capacitance = 100e-15,
        pd_supply = full_scale_input_voltage, 
        output_vs = 1, 
        num_transistor = 3,
        enable_cds = False,
        dark_current_noise = 0.05,
        enable_dcnu = True,
        enable_prnu = True,
        dcnu_std = 0.001,
        fd_gain = conversion_gain,
        fd_noise = 0.01,
        fd_prnu_std = 0.001,
        sf_gain = 1.0,
        sf_noise = 0.001,
        sf_prnu_std = 0.001
    )

    print("3T-APS energy: ", aps_3t.energy())

    simulation_output = aps_3t.noise([photon_input])

    img_res = simulation_output[0]

    print("3T-APS noise simulation result shape: ", img_res.shape, "max_val: ", np.max(img_res))

    cv2.imshow("image after adc", img_res/np.max(img_res))
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def test_4t_aps(img_name):
    img = np.array(cv2.imread(img_name, cv2.IMREAD_GRAYSCALE))
    # sensor specs
    full_scale_input_voltage = 1.8 # V
    pixel_full_well_capacity = 10000 # e
    conversion_gain = full_scale_input_voltage/pixel_full_well_capacity

    photon_input = img/255*pixel_full_well_capacity

    aps_4t = ActivePixelSensor(
        # performance parameters
        pd_capacitance = 100e-15,
        pd_supply = full_scale_input_voltage, 
        output_vs = 1, 
        num_transistor = 4,
        enable_cds = True,
        dark_current_noise = 0.05,
        enable_dcnu = True,
        enable_prnu = True,
        dcnu_std = 0.001,
        fd_gain = conversion_gain,
        fd_noise = 0.01,
        fd_prnu_std = 0.001,
        sf_gain = 1.0,
        sf_noise = 0.001,
        sf_prnu_std = 0.001
    )

    print("4T-APS energy: ", aps_4t.energy())

    simulation_output = aps_4t.noise([photon_input])

    img_res = simulation_output[0]

    print("4T-APS noise simulation result shape: ", img_res.shape, "max_val: ", np.max(img_res))

    cv2.imshow("image after adc", img_res/np.max(img_res))
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def test_dps(img_name):
    img = np.array(cv2.imread(img_name, cv2.IMREAD_GRAYSCALE))

    # sensor specs
    full_scale_input_voltage = 1.8 # V
    pixel_full_well_capacity = 10000 # e
    conversion_gain = full_scale_input_voltage/pixel_full_well_capacity

    photon_input = img/255*pixel_full_well_capacity

    dps = DigitalPixelSensor(
        # performance parameters
        pd_supply = 1.8, # [V]
        num_transistor = 4,
        enable_cds = True,
        # ADC performance parameters
        adc_type='SS',
        adc_fom=100e-15,  # [J/conversion]
        adc_reso=8,
        # noise parameters
        dark_current_noise = 0.01,
        enable_dcnu = True,
        enable_prnu = True,
        dcnu_std = 0.001,
        # FD parameters
        fd_gain = conversion_gain,
        fd_noise = 0.005,
        fd_prnu_std = 0.001,
        # SF parameters
        sf_gain = 1.0,
        sf_noise = 0.005,
        sf_prnu_std = 0.001,
        # CDS parameters
        cds_gain = 1.0,
        cds_noise = 0.005,
        cds_prnu_std = 0.001,
        # ADC parameters
        adc_noise = 0.005,
    )

    print("DPS energy: ", dps.energy())

    simulation_output = dps.noise([photon_input])

    img_res = simulation_output[0]

    print("DPS noise simulation result shape: ", img_res.shape, "max_val: ", np.max(img_res))

    cv2.imshow("image after adc", img_res/np.max(img_res))
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == '__main__':

    img_name = "../test_imgs/test_img.jpeg"
    
    # test_3t_aps(img_name)
    # test_4t_aps(img_name)
    test_dps(img_name)