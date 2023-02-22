
# import local modules
from enum_const import ProcessorLocation, ProcessDomain
from memory import FIFO, DoubleBuffer
from hw_compute import ADC, ComputeUnit, SystolicArray


# an example of user defined hw configuration setup 
def hw_config():

	compute_op_power = 1

	hw_dict = {
		"memory": [],
		"compute": [] 
	}

	double_buffer = DoubleBuffer(
		name="DoubleBuffer",
		size=(1, 1, 1280),
		clock = 500, 	# MHz
		read_port = 128,
		write_port = 128,
		read_write_port = 128,
		write_energy = 0.5,
		read_energy = 0.5,
		access_units = ["CompUnit", "SampleUnit", "ADC"],
		location = ProcessorLocation.COMPUTE_LAYER,
	)
	hw_dict["memory"].append(double_buffer)

	adc = ADC(
		name = "ADC",
		type = 1, # this needs to be fixed, use some enum.
		pixel_adc_ratio = (1, 720, 1),
		output_throughput = (1280, 1, 1), # redundent
		location = ProcessorLocation.SENSOR_LAYER,
	)
	adc.set_output_buffer(double_buffer)
	hw_dict["compute"].append(adc)

	comp_unit = ComputeUnit(
		name="CompUnit",
		domain=ProcessDomain.DIGITAL,
		location=ProcessorLocation.COMPUTE_LAYER,
		input_throughput = [(32, 1, 3)],
		output_throughput = (8, 1, 1),
		clock = 500, # MHz
		energy = 64*4*compute_op_power,
		area = 10,
		initial_delay = 0,
		delay = 4,
	)
	comp_unit.set_input_buffer(double_buffer)
	comp_unit.set_output_buffer(double_buffer)
	hw_dict["compute"].append(comp_unit)

	sampler_unit = ComputeUnit(
		name="SampleUnit",
		domain=ProcessDomain.DIGITAL,
		location=ProcessorLocation.COMPUTE_LAYER,
		input_throughput = [(16, 1, 3)],
		output_throughput = (8, 1, 3),
		clock = 500, # MHz
		energy = 8*2*compute_op_power,
		area = 10,
		initial_delay = 0,
		delay = 2,
	)
	sampler_unit.set_input_buffer(double_buffer)
	sampler_unit.set_output_buffer(double_buffer)
	hw_dict["compute"].append(sampler_unit)

	return hw_dict
