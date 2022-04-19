
class ProcessStage(object):
	"""docstring for ProcessStage"""
	def __init__(
		self, 
		name, 
		input_type,
		input_size,
		output_type,
		output_size
	):
		super(ProcessStage, self).__init__()
		self.name = name
		self.input_type = input_type
		self.input_size = input_size
		self.output_type = output_type
		self.output_size = output_size
		self.input_stages = []

	def set_input_stage(stage):
		self.input_stages.append(stage)
		

class DNNProcessStage(object):
	"""docstring for DNNProcessStage"""
	def __init__(
		self,
		name,
		ifmap_size,
		kernel_size,
		strike
	):
		super(DNNProcessStage, self).__init__()
		self.name = name 
		self.ifmap_size = ifmap_size
		self.kernel_size = kernel_size
		self.strike = strike
		self.input_stages = []

	def set_input_stage(stage):
		self.input_stages.append(stage)
		

input_data = Data((240, 160, 3))

denoise_stage = ProcessStage(
	name = "denoise",
	input_type = [PIXEL],
	input_size = [3], # every cycle load 3 elements
	output_type = [PIXEL],
	output_size = [1] # every cycle output 1 element
)

white_balance_stage = ProcessStage(
	name = "white_balance",
	input_type = [PIXEL],
	input_size = [1],
	output_type = [PIXEL],
	output_size = [1],
)

conv2d_1_stage = DNNProcessStage(
	name = "conv2d_1",
	ifmap_size = [240, 160, 3],
	kernel_size = [3, 3, 3, 32],
	strike = 2
)

denoise_stage.set_input_stage(input_data)
white_balance_stage.set_input_stage(denoise_stage)
conv2d_1_stage.set_input_stage(white_balance_stage)






