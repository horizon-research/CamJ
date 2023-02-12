import os
import sys
# directory reach
directory = os.getcwd()
parent_directory = os.path.dirname(directory)
# setting path
sys.path.append(os.path.dirname(directory))
sys.path.append(os.path.dirname(parent_directory))


from sim_core.analog_infra import AnalogArray, AnalogComponent
from sim_core.enum_const import ProcessorLocation, ProcessDomain
from sim_core.analog_utils import launch_analog_simulation
from sim_core.analog_lib import ActivePixelSensor, ActiveAnalogMemory, ColumnAmplifier, Comparator

from functional_core.launch import customized_eventification_simulation

from ieee_vr22.mapping_file import mapping_function_w_analog
from ieee_vr22.sw_pipeline import sw_pipeline_w_analog
from ieee_vr22.functional_pipeline import sensor_functional_pipeline, eventification_functional_pipeline


def analog_config():

	analog_arrays = []

	pixel_array = AnalogArray(
		name = "PixelArray",
		layer = ProcessorLocation.SENSOR_LAYER,
		num_input = [(32, 1, 1)],
		num_output = (32, 1, 1),
		functional_pipeline = sensor_functional_pipeline()
	)
	pixel = AnalogComponent(
		name = "BinningPixel",
		input_domain =[ProcessDomain.OPTICAL],
		output_domain = ProcessDomain.VOLTAGE,
		energy_func_list = [
			(
				ActivePixelSensor(
					pd_capacitance = 1e-12,
					pd_supply = 1.8, # V
					output_vs = 1, #  
					num_transistor = 3,
					num_readout = 1
				).energy,
				1
			)
		],
		num_input = [(1, 1)],
		num_output = (1, 1)
	)

	pixel_array.add_component(pixel, (32, 32, 1))
	pixel_array.set_source_component([pixel])
	pixel_array.set_destination_component([pixel])

	analog_arrays.append(pixel_array)

	return analog_arrays

	
if __name__ == '__main__':
	analog_arrays = analog_config()

	sw_stages = sw_pipeline_w_analog()

	mapping_dict = mapping_function_w_analog()

	total_energy = launch_analog_simulation(analog_arrays, sw_stages, mapping_dict)
	print("total energy:", total_energy)

	


