
class ProcessStage(object):
	"""docstring for ProcessStage"""
	def __init__(
		self, 
		name: str,
		input_type: list,
		input_size: list,
		input_throughput: list,
		output_type: list,
		output_size: list,
		output_throughput: list
	):
		super(ProcessStage, self).__init__()
		self.name = name
		self.input_type = input_type
		self.input_size = input_size
		self.input_throughput = input_throughput
		self.output_type = output_type
		self.output_size = output_size
		self.output_throughput = output_throughput 
		self.input_stages = []

	def set_input_stage(stage):
		self.input_stages.append(stage)
		
compute_sum = ProcessStage(
	name = "ComputeSum16",
	input_type = [VOLTAGE],
	input_size = [(1024, 1024)],
	input_throughput = [(4, 4)],
	output_type = [VOLTAGE],
	output_size = [(256, 256)], 
	output_throughput = [(1, 1)]
)

div_16 = ProcessStage(
	name = "DivBy16",
	input_type = [VOLTAGE],
	input_size = [(256, 256)],
	input_throughput = [(1, 1)],
	output_type = [DIGITAL],
	output_size = [(256, 256)], 
	output_throughput = [(1, 1)]
)


input_data = Voltage((1024, 1024))
compute_sum.set_input_stage(input_data)
div_16.set_input_stage(compute_sum)

class DNNProcessStage(object):
	"""docstring for DNNProcessStage"""
	def __init__(
		self,
		name: str,
		ifmap_size: list,
		kernel_size: list,
		strike: int,
		output_throughput: int
	):
		super(DNNProcessStage, self).__init__()
		self.name = name 
		self.ifmap_size = ifmap_size
		self.kernel_size = kernel_size
		self.strike = strike
		self.output_throughput = output_throughput
		self.input_stages = []

	def set_input_stage(stage):
		self.input_stages.append(stage)

conv2d_1_stage = DNNProcessStage(
	name = "Conv2D_1",
	ifmap_size = [240, 160, 3],
	kernel_size = [3, 3, 3, 32],
	strike = 2,
	self.output_throughput = 8,
)

conv2d_1_stage.set_input_stage(div_16)






