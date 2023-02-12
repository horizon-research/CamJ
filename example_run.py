from pprint import pprint
import numpy as np
import cv2


# import local modules
from sim_core.launch import launch_simulation
from functional_core.launch import launch_functional_simulation, customized_eventification_simulation

# from isscc_22_08v.mapping_file import mapping_function
# from isscc_22_08v.sw_pipeline import sw_pipeline
# from isscc_22_08v.hw_config import hw_config

from ieee_vr22.mapping_file import mapping_function, mapping_function_w_analog
from ieee_vr22.sw_pipeline import sw_pipeline, sw_pipeline_w_analog
from ieee_vr22.hw_config import hw_config, hw_config_w_analog


# from isscc_16_1_42.mapping_file import mapping_function
# from isscc_16_1_42.sw_pipeline import sw_pipeline
# from isscc_16_1_42.hw_config import hw_config

# from isscc_17_0_62.mapping_file import mapping_function
# from isscc_17_0_62.sw_pipeline import sw_pipeline
# from isscc_17_0_62.hw_config import hw_config

# from isscc_08_iVisual.mapping_file import mapping_function
# from isscc_08_iVisual.sw_pipeline import sw_pipeline
# from isscc_08_iVisual.hw_config import hw_config

# from isscc_13_reconfigurable.mapping_file import mapping_function
# from isscc_13_reconfigurable.sw_pipeline import sw_pipeline
# from isscc_13_reconfigurable.hw_config import hw_config

# from isscc_21_back_illuminated.mapping_file import mapping_function
# from isscc_21_back_illuminated.sw_pipeline import sw_pipeline
# from isscc_21_back_illuminated.hw_config import hw_config

# from rhythmic_pixel_21.mapping_file import mapping_function
# from rhythmic_pixel_21.sw_pipeline import sw_pipeline
# from rhythmic_pixel_21.hw_config import hw_config

# from simple_img_pipeline.mapping_file import mapping_function
# from simple_img_pipeline.sw_pipeline import sw_pipeline
# from simple_img_pipeline.hw_config import hw_config

# from simple_systolic_array.mapping_file import mapping_function
# from simple_systolic_array.sw_pipeline import sw_pipeline
# from simple_systolic_array.hw_config import hw_config

def eventification_noise_simulation_example(
	prev_img_name,
	curr_img_name,
	hw_dict,
	mapping_dict,
	sw_stage_list
):

	# sensor specs
	full_scale_input_voltage = 1.2 # V
	pixel_full_well_capacity = 10000 # e

	# load test image
	curr_img = np.array(cv2.imread(curr_img_name, cv2.IMREAD_GRAYSCALE))
	# a simple inverse img to photon
	photon_input = curr_img/255*pixel_full_well_capacity

	prev_img = np.array(cv2.imread(prev_img_name, cv2.IMREAD_GRAYSCALE))/255*full_scale_input_voltage

	input_mapping = {
		"CurrInput" : photon_input,
		"PrevResizedInput" : prev_img
	}

	simulation_res = launch_functional_simulation(sw_stage_list, hw_dict, mapping_dict, input_mapping)
	pprint(simulation_res)

	img_after_adc = simulation_res['CurrInput'][0]

	cv2.imshow("image after adc", img_after_adc/np.max(img_after_adc))
	cv2.waitKey(0)
	cv2.destroyAllWindows()


def main():

	hw_dict = hw_config_w_analog()
	mapping_dict = mapping_function_w_analog()
	sw_stage_list = sw_pipeline_w_analog()

	# hw_dict = hw_config()
	# mapping_dict = mapping_function()
	# sw_stage_list = sw_pipeline()

	# eventification simulation
	eventification_noise_simulation_example(
		prev_img_name = "test_imgs/test_eye1.png",
		curr_img_name = "test_imgs/test_eye2.png",
		hw_dict = hw_dict,
		mapping_dict = mapping_dict,
		sw_stage_list = sw_stage_list
	)

	exit()
	
	launch_simulation(
		hw_dict = hw_dict,
		mapping_dict = mapping_dict,
		sw_stage_list = sw_stage_list
	)
	exit()

if __name__ == '__main__':
	main()
