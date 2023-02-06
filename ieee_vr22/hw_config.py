
# import local modules
from sim_core.enum_const import ProcessorLocation, ProcessDomain
from sim_core.digital_memory import FIFO, DoubleBuffer
from sim_core.digital_compute import ADC, ComputeUnit, SystolicArray


# an example of user defined hw configuration setup 
def hw_config():

	compute_op_power = 0.5 # pJ 65nm 

	hw_dict = {
		"memory": [],
		"compute": [] 
	}

	fifo_buffer2 = FIFO(
		name="FIFO_INIT",
		hw_impl = "sram",
		count = 1280,
		clock = 500, 	# MHz
		write_energy = 3,
		read_energy = 1,
		location = ProcessorLocation.COMPUTE_LAYER,
		duplication = 100,
		write_unit = "ADC",
		read_unit = "ResizeUnit"
	)
	hw_dict["memory"].append(fifo_buffer2)
 
	fifo_buffer = FIFO(
		name="FIFO",
		hw_impl = "sram",
		count = 1280,
		clock = 500, 	# MHz
		write_energy = 3,
		read_energy = 1,
		location = ProcessorLocation.COMPUTE_LAYER,
		duplication = 100,
		write_unit = "ResizeUnit",
		read_unit = "Eventification"
	)
	hw_dict["memory"].append(fifo_buffer)

	double_buffer = DoubleBuffer(
		name="DoubleBuffer",
		size=(4, 4, 4096),
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
		output_throughput = (640, 1, 1),
		location = ProcessorLocation.SENSOR_LAYER,
	)
	adc.set_output_buffer(fifo_buffer2)
	hw_dict["compute"].append(adc)

	resize_unit = ComputeUnit(
	 	name="ResizeUnit",
		domain=ProcessDomain.DIGITAL,
		location=ProcessorLocation.SENSOR_LAYER,
		input_throughput = [(32, 2, 1)],
		output_throughput = (16, 1, 1), 
		clock = 500, # MHz
		energy = 16*3*compute_op_power,
		area = 10,
		initial_delay = 0,
		delay = 3,
	)
	hw_dict["compute"].append(resize_unit)

	resize_unit.set_input_buffer(fifo_buffer2)
	resize_unit.set_output_buffer(fifo_buffer)

	eventification_unit = ComputeUnit(
	 	name="Eventification",
		domain=ProcessDomain.DIGITAL,
		location=ProcessorLocation.SENSOR_LAYER,
		input_throughput = [(32, 1, 1), (32, 1, 1)],
		output_throughput = (32, 1, 1), 
		clock = 500, # MHz
		energy = 32*compute_op_power,
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
		input_throughput = [(4, 1, 1), (320, 200, 1)],
		output_throughput = (1, 1, 1), 
		clock = 500, # MHz
		energy = 320*200*compute_op_power,
		area = 10,
		initial_delay = 0,
		delay = 640,
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
		energy=16*16*compute_op_power,
		area=160
	)
	hw_dict["compute"].append(in_sensor_dnn_acc)

	in_sensor_dnn_acc.set_input_buffer(double_buffer)
	in_sensor_dnn_acc.set_output_buffer(double_buffer)

	return hw_dict
