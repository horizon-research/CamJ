

class DigitalStorage(object):
	"""docstring for DataStorage"""
	def __init__(
		self, 
		storage_type: int,
		impl: int,
		size: tuple,
		mem_technology: int, # this will specify the bandwitdh, latency, etc.
		port: int,
		port_accessibility: int,
		access_stage: list,
		location: int,
	):
		super(DigitalStorage, self).__init__()
		self.type = storage_type
		self.impl = impl
		self.size = size
		self.mem_technology = mem_technology
		self.port = port
		self.port_accessibility = port_accessibility
		self.access_stage = access_stage
		self.location = location


line_buffer1 = DigitalStorage(
	type = LINE_BUFFER,
	impl = SRAM,
	mem_technology = ??,
	port = [4],
	port_accessibility = [SHARED],
	access_stage = ["DivBy16", "Conv2D_1"],
	location = COMPUTE_LAYER,
)

scratchpad1 = DigitalStorage(
	type = SCRATCHPAD,
	impl = SRAM,
	mem_technology = ??,
	port = [4],
	port_accessibility = [SHARED],
	access_stage = ["Conv2D_1"],
	location = STORAGE_LAYER,
)

class ADC(object):
	"""docstring for ADC"""
	def __init__(
		self,
		type: INT,
		pixel_adc_ratio: tuple,
		location = location
	):
		super(ADC, self).__init__()
		self.type
		self.pixel_adc_ratio
		self.location = location

adc = ADC(
	SINGLE_SLOPE, # ADC type?
	pixel_adc_ratio=(1, 256), # or (1, 1), (4, 4)
	location=SENSOR_LAYER,
)

class ProcessUnit(object):
	"""docstring for ProcessUnit"""
	def __init__(
		self,
		name: str,
		domain: int,
		location: int,
		throughput: float,
		latency: float,
		power: float,
		area: float,
	):
		super(ProcessUnit, self).__init__()

		self.name = name		
		self.domain = domain
		self.location = location
		self.throughput = throughput
		self.latency = latency
		self.power = power
		self.area = area

	def set_input_buffer(input_buffer):
		self.input_buffer = input_buffer

	def set_output_buffer(output_buffer):
		self.output_buffer = output_buffer

 compute_sum_16_unit = ProcessUnit(
 	name="ComputeSum16",
	domain=ANALOG,
	location=SENSOR_LAYER,
	throughput = ??,
	latency = ??,
	power = ??,
	area = ??
)

compute_sum_16_unit.set_input_buffer(input_data)
compute_sum_16_unit.set_output_buffer(adc)

div_by_16_unit = ProcessUnit(
	name="DivBy16",
	domain=DIGITAL,
	location=COMPUTE_LAYER,
	throughput = ??,
	latency = ??,
	power = ??,
	area = ??
)

div_by_16_unit.set_input_buffer(adc)
div_by_16_unit.set_output_buffer(line_buffer1)


conv2d_unit = ProcessUnit(
	name="Conv2D_1",
	domain=DIGITAL,
	location=COMPUTE_LAYER,
	throughput = ??,
	latency = ??,
	power = ??,
	area = ??
)

conv2d_unit.set_input_buffer(line_buffer1)
conv2d_unit.set_output_buffer(scratchpad1)

