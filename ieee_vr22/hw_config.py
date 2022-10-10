
# import local modules
from enum_const import ProcessorLocation, ProcessDomain
from memory import FIFO, DoubleBuffer
from hw_compute import ADC, ComputeUnit, SystolicArray


# an example of user defined hw configuration setup 
def hw_config():

	hw_dict = {
		"memory": [],
		"compute": [] 
	}

	fifo_buffer = FIFO(
		name="FIFO",
		hw_impl = "sram",
		count = 128,
		clock = 500, 	# MHz
		write_energy = 3,
		read_energy = 1,
		location = ProcessorLocation.COMPUTE_LAYER,
		duplication = 64,
		write_unit = "ADC",
		read_unit = "Eventification"
	)
	hw_dict["memory"].append(fifo_buffer)

	double_buffer = DoubleBuffer(
		name="DoubleBuffer",
		size=(4, 4, 1024),
		clock = 500, 	# MHz
		read_port = 16,
		write_port = 16,
		read_write_port = 16,
		write_energy = 3,
		read_energy = 1,
		access_units = ["ConvUnit", "InSensorSystolicArray"],
		location = ProcessorLocation.COMPUTE_LAYER,
	)
	hw_dict["memory"].append(double_buffer)

	adc = ADC(
		name = "ADC",
		type = 1, # this needs to be fixed, use some enum.
		pixel_adc_ratio = (1, 64, 1),
		output_throughput = (64, 1, 1), # redundent
		location = ProcessorLocation.SENSOR_LAYER,
	)
	adc.set_output_buffer(fifo_buffer)
	hw_dict["compute"].append(adc)

	eventification_unit = ComputeUnit(
	 	name="Eventification",
		domain=ProcessDomain.DIGITAL,
		location=ProcessorLocation.SENSOR_LAYER,
		input_throughput = [(32, 1, 1), (32, 1, 1)],
		output_throughput = (32, 1, 1), 
		clock = 500, # MHz
		energy = 32*4.6,
		area = 10,
		initial_delay = 0,
		delay = 1,
	)
	hw_dict["compute"].append(eventification_unit)

	eventification_unit.set_input_buffer(fifo_buffer)
	eventification_unit.set_output_buffer(double_buffer)

	thresholding_unit = ComputeUnit(
	 	name="ThresholdingUnit",
		domain=ProcessDomain.DIGITAL,
		location=ProcessorLocation.SENSOR_LAYER,
		input_throughput = [(4, 1, 1), (64, 64, 1)],
		output_throughput = (1, 1, 1), 
		clock = 500, # MHz
		energy = 64*4.6,
		area = 10,
		initial_delay = 0,
		delay = 64,
	)
	hw_dict["compute"].append(thresholding_unit)

	thresholding_unit.set_input_buffer(double_buffer)
	thresholding_unit.set_output_buffer(double_buffer)	

	in_sensor_dnn_acc = SystolicArray(
		name="InSensorSystolicArray",
		domain=ProcessDomain.DIGITAL,
		location=ProcessorLocation.COMPUTE_LAYER,
		size_dimension=(16, 16),
		clock=500,
		energy=16*16*4.6,
		area=160
	)
	hw_dict["compute"].append(in_sensor_dnn_acc)

	in_sensor_dnn_acc.set_input_buffer(double_buffer)
	in_sensor_dnn_acc.set_output_buffer(double_buffer)

	return hw_dict
