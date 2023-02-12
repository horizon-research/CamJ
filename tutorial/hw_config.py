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

	line_buffer1 = LineBuffer(
		name = "LineBuffer-1",
		size = (3, 32), 	# assume line buffer has three rows, each row can store 64 of data
		hw_impl = "sram",
		clock = 500, 	# MHz
		location = ProcessorLocation.COMPUTE_LAYER,
		write_energy = 3,
		read_energy = 1,
		duplication = 1,
		write_unit = "ADC",
		read_unit = "Conv1Unit"
	)
	hw_dict["memory"].append(line_buffer1)

	fifo_buffer1 = FIFO(
		name="FIFO-1",
		hw_impl = "sram",
		count = 32*32,
		clock = 500, 	# MHz
		write_energy = 3,
		read_energy = 1,
		location = ProcessorLocation.COMPUTE_LAYER,
		duplication = 1,
		write_unit = "Conv1Unit",
		read_unit = "Conv2Unit"
	)
	hw_dict["memory"].append(fifo_buffer1)

	fifo_buffer2 = FIFO(
		name="FIFO-2",
		hw_impl = "sram",
		count = 16,
		clock = 500, 	# MHz
		write_energy = 3,
		read_energy = 1,
		location = ProcessorLocation.COMPUTE_LAYER,
		duplication = 1,
		write_unit = "Conv2Unit",
		read_unit = "AbsUnit"
	)
	hw_dict["memory"].append(fifo_buffer2)

	fifo_buffer3 = FIFO(
		name="FIFO-3",
		hw_impl = "sram",
		count = 16*16,
		clock = 500, 	# MHz
		write_energy = 3,
		read_energy = 1,
		location = ProcessorLocation.COMPUTE_LAYER,
		duplication = 1,
		write_unit = "AbsUnit",
		read_unit = None
	)
	hw_dict["memory"].append(fifo_buffer3)

	adc = ADC(
		name = "ADC",
		type = 1, # this needs to be fixed, use some enum.
		pixel_adc_ratio = (1, 32, 1),
		output_throughput = (32, 1, 1),
		location = ProcessorLocation.SENSOR_LAYER,
	)
	adc.set_output_buffer(line_buffer1)
	hw_dict["compute"].append(adc)

	conv1_unit = ComputeUnit(
	 	name="Conv1Unit",
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
	hw_dict["compute"].append(conv1_unit)

	conv1_unit.set_input_buffer(line_buffer1)
	conv1_unit.set_output_buffer(fifo_buffer1)

	conv2_unit = ComputeUnit(
	 	name="Conv2Unit",
		domain=ProcessDomain.DIGITAL,
		location=ProcessorLocation.SENSOR_LAYER,
		input_throughput = [(2, 2, 1)],
		output_throughput = (1, 1, 1), 
		clock = 500, # MHz
		energy = 1,
		area = 10,
		initial_delay = 2,
		delay = 1,
	)
	hw_dict["compute"].append(conv2_unit)

	conv2_unit.set_input_buffer(fifo_buffer1)
	conv2_unit.set_output_buffer(fifo_buffer2)

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
	abs_unit.set_input_buffer(fifo_buffer2)
	abs_unit.set_output_buffer(fifo_buffer3)
	hw_dict["compute"].append(abs_unit)

	return hw_dict
