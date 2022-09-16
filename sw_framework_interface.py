
class PixelInput(object):
	def __init__(
		self,
		size,
		name
	):

		self.size = size
		self.output_size = size
		self.input_stages = []
		self.name = name
		self.output_stages = []
		self.ready_board = {}

	def __str__(self):
		return self.name

	def __repr__(self):
		return self.name

	def set_output_stage(self, stage):
		self.output_stages.append(stage)

	def check_ready_board(self):
		return True


class ProcessStage(object):
	"""docstring for ProcessStage"""
	def __init__(
		self, 
		name: str,
		input_size: list,
		output_size: list
	):
		super(ProcessStage, self).__init__()
		self.name = name
		self.input_size = input_size
		self.output_size = output_size
		self.input_stages = []
		self.output_stages = []
		self.ready_board = {}

	def set_input_stage(self, stage):
		self.input_stages.append(stage)

	def set_output_stage(self, stage):
		self.output_stages.append(stage)

	def is_parent_of(self, process_stage):

		if process_stage in self.input_stages:
			return True
		else:
			return False

	def is_child_process_of(self, process_stage):

		if process_stage in self.input_stages:
			return True
		else:
			return False

	def construct_ready_board(self, stage):
		self.ready_board[stage] = False

	def set_ready_board(self, stage):
		self.ready_board[stage] = True

	def check_ready_board(self):
		for k in self.ready_board:
			if self.ready_board[k] == False:
				return False

		return True

	def __str__(self):
		return self.name

	def __repr__(self):
		return self.name		

class DNNProcessStage(object):
	"""docstring for DNNProcessStage"""
	def __init__(
		self,
		name: str,
		op_type: str,
		ifmap_size: list,
		kernel_size: list,
		stride: int
	):
		super(DNNProcessStage, self).__init__()
		self.name = name
		self.type = op_type 
		self.ifmap_size = ifmap_size
		self.kernel_size = kernel_size
		self.stride = stride
		self.input_stages = []
		self.output_stages = []
		self.ready_board = {}

		if op_type == "Conv2D":
			self.output_size = (
				int(self.ifmap_size[0]/self.stride), 
				int(self.ifmap_size[1]/self.stride), 
				int(self.kernel_size[-1])
			)
		elif op_type == "FC":
			self.output_size = (
				int(self.kernel_size[1]),
				1,
				1
			)
		else:
			raise Exception("Unsupported op types.")

	def flatten():
		size = 1
		for i in len(self.output_size):
			size *= self.output_size[i]

		self.output_size = (size, 1)

	def set_input_stage(self, stage):
		self.input_stages.append(stage)

	def set_output_stage(self, stage):
		self.output_stages.append(stage)

	def is_parent_of(self, process_stage):

		if process_stage in self.input_stages:
			return True
		else:
			return False

	def is_child_process_of(self, process_stage):

		if process_stage in self.input_stages:
			return True
		else:
			return False

	def construct_ready_board(self, stage):
		self.ready_board[stage] = False

	def set_ready_board(self, stage):
		self.ready_board[stage] = True

	def check_ready_board(self):
		for k in self.ready_board:
			if self.ready_board[k] == False:
				return False

		return True

	def __str__(self):
		return self.name

	def __repr__(self):
		return self.name

def find_src_stages(sw_stage_list):

	parent_stages = []
	prev_parent_stages = []
	for sw_stage in sw_stage_list:
		prev_parent_stages.append(sw_stage)

	for i in range(len(sw_stage_list)):
		for sw_stage in prev_parent_stages:
			if len(sw_stage.input_stages) == 0:
				if sw_stage not in parent_stages:
					parent_stages.append(sw_stage)
			else:
				for curr_parent_stage in sw_stage.input_stages:
					if curr_parent_stage not in parent_stages:
						if curr_parent_stage not in parent_stages:
							parent_stages.append(curr_parent_stage)

		prev_parent_stages = []
		for stage in parent_stages:
			prev_parent_stages.append(stage)

		parent_stages = []

	return prev_parent_stages

def find_dst_stages(sw_stage_list):

	child_stages = []

	for child_stage in  sw_stage_list:
		is_child_stage = True
		for sw_stage in sw_stage_list:
			if child_stage in sw_stage.input_stages:
				is_child_stage = False
				break

		if is_child_stage:
			child_stages.append(child_stage)

	return child_stages

def set_output_stages(sw_stage_list):
	for sw_stage in sw_stage_list:
		for in_stage in sw_stage.input_stages:
			in_stage.set_output_stage(sw_stage)

def build_ready_board(sw_stage_list):
	for sw_stage in sw_stage_list:
		for in_stage in sw_stage.input_stages:
			sw_stage.construct_ready_board(in_stage)

def build_sw_graph(sw_stage_list):

	set_output_stages(sw_stage_list)
	build_ready_board(sw_stage_list)

	for sw_stage in sw_stage_list:
		print(sw_stage, ": ", sw_stage.output_stages)

	# exit()

	root_src_stage = find_src_stages(sw_stage_list)
	root_dst_stage = find_dst_stages(sw_stage_list)

	print("root source: ", root_src_stage)
	print("root target: ", root_dst_stage)

	graph_layers = []
	ready_list = []

	i = 0

	while len(ready_list) != len(sw_stage_list):
		i += 1
		print("###### Pipeline %d ######" % i)

		curre_stage_layer = []

		for sw_stage in sw_stage_list:
			if sw_stage not in ready_list:
				if sw_stage.check_ready_board():
					ready_list.append(sw_stage)
					curre_stage_layer.append(sw_stage)
					# for out_stage in sw_stage.output_stages:
					# out_stage.set_ready_board(sw_stage)

		for sw_stage in curre_stage_layer:
			for out_stage in sw_stage.output_stages:
				out_stage.set_ready_board(sw_stage)
				print("src: ", sw_stage, "dst: ", out_stage)


		print(curre_stage_layer)
		graph_layers.append(curre_stage_layer)

		








