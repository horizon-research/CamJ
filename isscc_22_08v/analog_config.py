import os
import sys
# directory reach
directory = os.getcwd()
parent_directory = os.path.dirname(directory)
# setting path
sys.path.append(os.path.dirname(directory))
sys.path.append(os.path.dirname(parent_directory))


from analog_infra import AnalogArray, AnalogComponent
from enum_const import ProcessorLocation, ProcessDomain
from analog_utils import check_analog_connect_consistency, compute_total_energy

def dummy_energy_func():
	return 1

def analog_config():

	analog_arrays = []

	pixel_array = AnalogArray(
		name = "PixelArray",
		layer = ProcessorLocation.SENSOR_LAYER,
		num_input = [(3, 126)],
		num_output = (3, 126)
	)
	pixel = AnalogComponent(
		name = "Pxiel",
		input_domain =[ProcessDomain.OPTICAL],
		output_domain = ProcessDomain.TIME,
		energy = dummy_energy_func
	)

	pixel_array.add_component(pixel, (126, 126))
	pixel_array.set_source_component([pixel])
	pixel_array.set_destination_component([pixel])

	analog_weight = AnalogArray(
		name = "AnalogWeight",
		layer = ProcessorLocation.SENSOR_LAYER,
		num_input = None,
		num_output = (3, 3)
	)
	current_dac = AnalogComponent(
		name = "CurrentDAC",
		input_domain = [ProcessDomain.DIGITAL],
		output_domain = ProcessDomain.CURRENT,
		energy = dummy_energy_func
	)
	
	analog_weight.add_component(current_dac, (3, 3))
	analog_weight.set_source_component([current_dac])
	analog_weight.set_destination_component([current_dac])


	pe_array = AnalogArray(
		name = "PEArray",
		layer = ProcessorLocation.SENSOR_LAYER,
		num_input = [(3, 3), (3, 126)],
		num_output = (1, 42)
	)

	pe = AnalogComponent(
		name = "PE",
		input_domain = [ProcessDomain.CURRENT, ProcessDomain.TIME],
		output_domain = ProcessDomain.DIGITAL,
		energy = dummy_energy_func,
		num_input = [(3, 3), (3, 3)],
		num_output = (1, 1)
	)

	pe_array.add_component(pe, (1, 42))
	pe_array.set_source_component([pe])
	pe_array.set_destination_component([pe])

	pe_array.add_input_array(pixel_array)
	pe_array.add_input_array(analog_weight)

	pixel_array.add_output_array(pe_array)
	analog_weight.add_output_array(pe_array)

	analog_arrays.append(pixel_array)
	analog_arrays.append(analog_weight)
	analog_arrays.append(pe_array)

	return analog_arrays

	
if __name__ == '__main__':
	analog_arrays = analog_config()

	check_analog_connect_consistency(analog_arrays)

	total_energy = compute_total_energy(analog_arrays)
	print("total energy:", total_energy)
