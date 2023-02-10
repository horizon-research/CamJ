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


from ieee_vr22.mapping_file import mapping_function_w_analog
from ieee_vr22.sw_pipeline import sw_pipeline_w_analog

def dummy_energy_func():
	return 1

def analog_config():

	analog_arrays = []

	pixel_array = AnalogArray(
		name = "PixelArray",
		layer = ProcessorLocation.SENSOR_LAYER,
		num_input = [(640, 2, 1)],
		num_output = (320, 1, 1)
	)
	pixel = AnalogComponent(
		name = "BinningPixel",
		input_domain =[ProcessDomain.OPTICAL],
		output_domain = ProcessDomain.VOLTAGE,
		energy = dummy_energy_func,
		num_input = [(2, 2)],
		num_output = (1, 1)
	)

	pixel_array.add_component(pixel, (320, 200, 1))
	pixel_array.set_source_component([pixel])
	pixel_array.set_destination_component([pixel])

	analog_memory_array = AnalogArray(
		name = "AnalogMemoryArray",
		layer = ProcessorLocation.SENSOR_LAYER,
		num_input = [],
		num_output = [(320, 1, 1)],
	)

	analog_memory_unit = AnalogComponent(
		name = "AnalogMemoryunit",
		input_domain = [],
		output_domain = ProcessDomain.VOLTAGE,
		energy = dummy_energy_func,
		num_input = [],
		num_output = [(1, 1)]
	)

	analog_memory_array.add_component(analog_memory_unit, (320, 201))
	analog_memory_array.set_source_component([analog_memory_unit])
	analog_memory_array.set_destination_component([analog_memory_unit])

	eventification_array = AnalogArray(
		name = "EventificationArray",
		layer = ProcessorLocation.SENSOR_LAYER,
		num_input = [(320, 1), (320, 1)],
		num_output = (320, 1)
	)
	eventification_pe = AnalogComponent(
		name = "EventificationPE",
		input_domain = [ProcessDomain.VOLTAGE, ProcessDomain.VOLTAGE],
		output_domain = ProcessDomain.VOLTAGE,
		energy = dummy_energy_func,
		num_input = [(1, 1), (1, 1)],
		num_output = (1, 1)
	)
	
	eventification_array.add_component(eventification_pe, (320, 1))
	eventification_array.set_source_component([eventification_pe])
	eventification_array.set_destination_component([eventification_pe])

	pixel_array.add_output_array(eventification_array)
	eventification_array.add_input_array(pixel_array)

	analog_memory_array.add_output_array(eventification_array)
	eventification_array.add_input_array(analog_memory_array)

	analog_arrays.append(pixel_array)
	analog_arrays.append(analog_memory_array)
	analog_arrays.append(eventification_array)

	return analog_arrays

	
if __name__ == '__main__':
	analog_arrays = analog_config()

	sw_stages = sw_pipeline_w_analog()

	mapping_dict = mapping_function_w_analog()

	total_energy = launch_analog_simulation(analog_arrays, sw_stages, mapping_dict)
	print("total energy:", total_energy)

	


