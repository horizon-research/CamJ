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
from memory import FIFO, LineBuffer
from hw_compute import ADC, ComputeUnit


# an example of user defined hw configuration setup 
def hw_config():

	hw_dict = {
		"memory": [],
		"compute": [],
	}

	line_buffer = LineBuffer(
		name = "LineBuffer",
		size = (3, 32), 	# assume line buffer has three rows, each row can store 64 of data
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

	fifo_buffer = FIFO(
		name="FIFO",
		hw_impl = "sram",
		count = 32,
		clock = 500, 	# MHz
		write_energy = 3,
		read_energy = 1,
		location = ProcessorLocation.COMPUTE_LAYER,
		duplication = 1,
		write_unit = "ConvUnit",
		read_unit = "AbsUnit"
	)
	hw_dict["memory"].append(fifo_buffer)

	fifo_buffer2 = FIFO(
		name="FIFO2",
		hw_impl = "sram",
		count = 30*30,
		clock = 500, 	# MHz
		write_energy = 3,
		read_energy = 1,
		location = ProcessorLocation.COMPUTE_LAYER,
		duplication = 1,
		write_unit = "AbsUnit",
		read_unit = None
	)
	hw_dict["memory"].append(fifo_buffer2)

	adc = ADC(
		name = "ADC",
		type = 1, # this needs to be fixed, use some enum.
		pixel_adc_ratio = (1, 32, 1),
		output_throughput = (30, 1, 1), # redundent
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
	conv_unit.set_output_buffer(fifo_buffer)

	abs_unit = ComputeUnit(
		name="AbsUnit",
		domain=ProcessDomain.DIGITAL,
		location=ProcessorLocation.COMPUTE_LAYER,
		input_throughput = [(1, 1, 1)],
		output_throughput = (1, 1, 1),
		clock = 500, # MHz
		energy = 1,
		area = 10,
		initial_delay = 0,
		delay = 1,
	)
	abs_unit.set_input_buffer(fifo_buffer)
	abs_unit.set_output_buffer(fifo_buffer2)
	hw_dict["compute"].append(abs_unit)

	return hw_dict
