
# import local modules
from enum_const import ProcessorLocation, ProcessDomain
from memory import Scratchpad
from hw_compute import ADC, ComputeUnit, SystolicArray


# an example of user defined hw configuration setup 
def hw_config():

	hw_dict = {
		"memory": [],
		"compute": [] 
	}

	in_sensor_buffer = Scratchpad(
		name = "InSensorBuffer",
		size = (2, 8, 512*512/8), 	# assume double buffer scratchpad with 8 banks each.
									# to store two 512x512 frames
		clock = 500, 	# MHz
		read_port = 64,
		write_port = 64,
		read_write_port = 64,
		access_units = ["EdgeDetection", "BBoxDetection", "Eventification", "Thresholding"
						"InSensorSystolicArray", "OffchipBuffer", "ADC"],
		write_energy = 3,
		read_energy = 1,
		location = ProcessorLocation.COMPUTE_LAYER
	)
	hw_dict["memory"].append(in_sensor_buffer)

	offchip_buffer = Scratchpad(
		name="OffchipBuffer",
		size = (2, 16, 1024*64), 	# assume double buffer scratchpad with 2MB size
		clock = 500, 	# MHz
		read_port = 256,
		write_port = 256,
		read_write_port = 256,
		access_units = ["InSensorBuffer", "NearSensorSystolicArray", "OffchipDRAM",
						"EdgeDetection", "BBoxDetection"],
		write_energy = 30,
		read_energy = 10,
		
		location = ProcessorLocation.COMPUTE_LAYER
	)
	hw_dict["memory"].append(offchip_buffer)

	adc = ADC(
		name = "ADC",
		type = 1, # this needs to be fixed, use some enum.
		pixel_adc_ratio = (1, 256, 1),
		output_throughput = (256, 1, 1), # redundent
		location = ProcessorLocation.SENSOR_LAYER,
	)
	adc.set_output_buffer(offchip_buffer)
	hw_dict["compute"].append(adc)

	eventification_unit = ComputeUnit(
	 	name="Eventification",
		domain=ProcessDomain.DIGITAL,
		location=ProcessorLocation.SENSOR_LAYER,
		input_throughput = [(32, 1, 1), (32, 1, 1)],
		output_throughput = (32, 1, 1), 
		clock = 500, # MHz
		energy = 1,
		area = 10,
		initial_delay = 0,
		delay = 1,
	)
	hw_dict["compute"].append(eventification_unit)

	eventification_unit.set_input_buffer(offchip_buffer)
	eventification_unit.set_output_buffer(in_sensor_buffer)

	thresholding_unit = ComputeUnit(
		name="Thresholding",
		domain=ProcessDomain.DIGITAL,
		location=ProcessorLocation.COMPUTE_LAYER,
		input_throughput = [(4, 1, 1), (4, 1, 1), (256, 256, 1)],
		output_throughput = (1, 1, 1),
		clock = 500, # MHz
		energy = 1,
		area = 10,
		initial_delay = 0,
		delay=1,
	)
	hw_dict["compute"].append(thresholding_unit)

	thresholding_unit.set_input_buffer(in_sensor_buffer)
	thresholding_unit.set_output_buffer(in_sensor_buffer)

	in_sensor_dnn_acc = SystolicArray(
		name="InSensorSystolicArray",
		domain=ProcessDomain.DIGITAL,
		location=ProcessorLocation.COMPUTE_LAYER,
		size_dimension=(16, 16),
		clock=500,
		energy=16,
		area=160
	)
	hw_dict["compute"].append(in_sensor_dnn_acc)

	in_sensor_dnn_acc.set_input_buffer(in_sensor_buffer)
	in_sensor_dnn_acc.set_output_buffer(in_sensor_buffer)

	offchip_dnn_acc = SystolicArray(
		name="NearSensorSystolicArray",
		domain=ProcessDomain.DIGITAL,
		location=ProcessorLocation.OFF_CHIP,
		size_dimension=(32, 32),
		clock=500,
		energy=64,
		area=640
	)
	hw_dict["compute"].append(offchip_dnn_acc)

	offchip_dnn_acc.set_input_buffer(offchip_buffer)

	offchip_dnn_acc.set_output_buffer(offchip_buffer)

	edge_detection_unit = ComputeUnit(
		name = "EdgeDetection",
		domain = ProcessDomain.DIGITAL,
		location = ProcessorLocation.OFF_CHIP,
		input_throughput = [(8, 8, 1)],
		output_throughput = (8, 8, 1),
		clock = 500, # MHz
		energy = 1,
		area = 5,
		initial_delay = 2,
		delay=1,
	)
	hw_dict["compute"].append(edge_detection_unit)

	edge_detection_unit.set_input_buffer(offchip_buffer)
	edge_detection_unit.set_output_buffer(in_sensor_buffer)

	bbox_detection_unit = ComputeUnit(
		name = "BBoxDetection",
		domain = ProcessDomain.DIGITAL,
		location = ProcessorLocation.OFF_CHIP,
		input_throughput = [(256, 256, 1)],
		output_throughput = (4, 1, 1),
		clock = 500, # MHz
		energy = 1,
		area = 15,
		initial_delay = 0,
		delay = 1
	)
	hw_dict["compute"].append(bbox_detection_unit)

	bbox_detection_unit.set_input_buffer(offchip_buffer)
	bbox_detection_unit.set_output_buffer(in_sensor_buffer)

	return hw_dict
