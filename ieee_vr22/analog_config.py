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
from ieee_vr22.noise_config import sensor_noise_model, eventification_noise_model


def dummy_energy_func():
	return 1

def analog_config():

	analog_arrays = []

	pixel_array = AnalogArray(
		name = "PixelArray",
		layer = ProcessorLocation.SENSOR_LAYER,
		num_input = [(640, 2, 1)],
		num_output = (320, 1, 1),
		functional_pipeline = sensor_noise_model()
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
		num_input = [(2, 2)],
		num_output = (1, 1)
	)

	pixel_array.add_component(pixel, (320, 200, 1))

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
		energy_func_list = [
			(ColumnAmplifier().energy, 1),
			(
				ActiveAnalogMemory(
					capacitance = 1e-12,
					t_sample = 1e-6,
					t_hold = 10e-3,
					supply = 1.8 # V
				).energy,
				1
			)
		],
		num_input = [],
		num_output = [(1, 1)]
	)
	analog_memory_array.add_component(analog_memory_unit, (320, 201))

	eventification_array = AnalogArray(
		name = "EventificationArray",
		layer = ProcessorLocation.SENSOR_LAYER,
		num_input = [(320, 1), (320, 1)],
		num_output = (320, 1),
		functional_pipeline = eventification_noise_model(),
		functional_sumication_func = customized_eventification_simulation
	)
	eventification_pe = AnalogComponent(
		name = "EventificationPE",
		input_domain = [ProcessDomain.VOLTAGE, ProcessDomain.VOLTAGE],
		output_domain = ProcessDomain.VOLTAGE,
		energy_func_list = [
			# SourceFollower().energy,
			# SourceFollower().energy,
			# SourceFollower().energy,
			(ColumnAmplifier().energy, 1),
			(ColumnAmplifier().energy, 1),
			(Comparator().energy, 1)
		],
		num_input = [(1, 1), (1, 1)],
		num_output = (1, 1)
	)
	eventification_array.add_component(eventification_pe, (320, 1))

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

	


