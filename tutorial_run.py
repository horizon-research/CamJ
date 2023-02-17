from pprint import pprint
import numpy as np
import cv2
import copy

# import local modules
from sim_core.launch import launch_simulation
from functional_core.launch import launch_functional_simulation

# import tutorial example configuration modules
from tutorial.mapping_file import mapping_function
from tutorial.sw_pipeline import sw_pipeline
from tutorial.hw_config import hw_config

# functional simulation harness function
def tutorial_functional_simulation(
	img_name,
	hw_dict,
	mapping_dict,
	sw_stage_list
):

	# sensor specs
	full_scale_input_voltage = 1.2 # V
	pixel_full_well_capacity = 10000 # e

	# load test image
	img = np.array(cv2.imread(img_name, cv2.IMREAD_GRAYSCALE))
	# a simple inverse img to photon
	photon_input = img/255*pixel_full_well_capacity

	input_mapping = {
		"Input" : [photon_input]
	}

	simulation_res = launch_functional_simulation(sw_stage_list, hw_dict, mapping_dict, input_mapping)

	img_after_adc = simulation_res['Input'][0]

	cv2.imshow("image after adc", img_after_adc/np.max(img_after_adc))
	cv2.waitKey(0)
	cv2.destroyAllWindows()

def main():

	hw_dict = hw_config()
	mapping_dict = mapping_function()
	sw_stage_list = sw_pipeline()

	tutorial_functional_simulation(
		img_name = "test_imgs/test_img.jpeg",
	    hw_dict = hw_dict,
		mapping_dict = mapping_dict,
		sw_stage_list = sw_stage_list
	)
	
	launch_simulation(
		hw_dict = hw_dict,
		mapping_dict = mapping_dict,
		sw_stage_list = sw_stage_list
	)

if __name__ == '__main__':
	main()
