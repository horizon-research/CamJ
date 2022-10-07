import os
import sys
# directory reach
directory = os.getcwd()
parent_directory = os.path.dirname(directory)
# setting path
sys.path.append(os.path.dirname(directory))
sys.path.append(os.path.dirname(parent_directory))

# import local modules
from enum_const import ProcessorLocation, ProcessDomain
from memory import FIFO, LineBuffer, DoubleBuffer
from hw_compute import ADC, ComputeUnit, SystolicArray


# an example of user defined hw configuration setup 
def hw_config():

	hw_dict = {
		"memory": [],
		"compute": [],
	}

	line_buffer = LineBuffer(
		name = "LineBuffer",
		size = (3, 64), 
		hw_impl = "sram",
		clock = 500, 	# MHz
		location = ProcessorLocation.COMPUTE_LAYER,
		write_energy = 3,
		read_energy = 1,
		duplication = 1,
		write_unit = "ADC",
		read_unit = "ConvUnit"
	)
	hw_dict["memory"].append(line_buffer)

	double_buffer = DoubleBuffer(
		name="DoubleBuffer",
		size=(4, 4, 256),
		clock = 500, 	# MHz
		read_port = 8,
		write_port = 8,
		read_write_port = 8,
		write_energy = 3,
		read_energy = 1,
		access_units = ["ConvUnit", "SystolicArray"],
		location = ProcessorLocation.COMPUTE_LAYER,
	)
	hw_dict["memory"].append(double_buffer)

	adc = ADC(
		name = "ADC",
		type = 1, # this needs to be fixed, use some enum.
		pixel_adc_ratio = (1, 66, 1),
		output_throughput = (64, 1, 1), # redundent
		location = ProcessorLocation.SENSOR_LAYER,
	)
	adc.set_output_buffer(line_buffer)
	hw_dict["compute"].append(adc)

	conv_unit = ComputeUnit(
	 	name="ConvUnit",
		domain=ProcessDomain.DIGITAL,
		location=ProcessorLocation.SENSOR_LAYER,
		input_throughput = [(1, 3, 1)],
		output_throughput = (1, 1, 1), 
		clock = 500, # MHz
		energy = 1,
		area = 10,
		initial_delay = 2,
		delay = 1,
	)
	hw_dict["compute"].append(conv_unit)

	conv_unit.set_input_buffer(line_buffer)
	conv_unit.set_output_buffer(double_buffer)

	dnn_acc = SystolicArray(
		name="SystolicArray",
		domain=ProcessDomain.DIGITAL,
		location=ProcessorLocation.COMPUTE_LAYER,
		size_dimension=(16, 16),
		clock=500,
		energy=16,
		area=160
	)
	hw_dict["compute"].append(dnn_acc)

	dnn_acc.set_input_buffer(double_buffer)
	dnn_acc.set_output_buffer(double_buffer)

	return hw_dict
