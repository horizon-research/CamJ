'''
	This file includes important functions that are used in simulation.
	Those function are the logic in the simulation and intentionally hidden from the users.

'''

import numpy as np



# this function creates the mapping from sw stage to hw unit.
# sw stage to hw unit is one-to-one mapping.
# hw unit to sw stage is one-to-multi mapping.
def map_sw_hw(mapping_dict, sw_stage_list, hw_dict):
	sw2hw = {}
	hw2sw = {}
	for k, v in mapping_dict.items():
		sw = None
		for sw_stage in sw_stage_list:
			if sw_stage.name == k:
				sw = sw_stage
				break

		hw = None
		for hw_unit in hw_dict["compute"]:
			if hw_unit.name == v:
				hw = hw_unit
				break

		if hw != None and sw != None:
			sw2hw[sw] = hw
			if hw in hw2sw:
				hw2sw[hw].append(sw)
			else:
				hw2sw[hw] = [sw]

	return sw2hw, hw2sw

'''
	This function is used to double check if the producer's output buffer is the same as 
	the cosumer's input buffer.
	This function is used after the computation graph is constructed.

'''
def check_buffer_consistency(src_unit, dst_unit):

	if src_unit.output_buffer == dst_unit.input_buffer:
		return True
	else:
		raise Exception("%s %s don't have a common buffer to commnicate!" % src_unit.name, dst_unit.name)

'''
	This function is used to connect the consumer and producer in the computational graph.
'''
def build_buffer_edges(sw_stage_list, hw_dict, sw2hw):

	buffer_edge_dict = {}

	for sw_stage in sw_stage_list:
		for output_stage in sw_stage.output_stages:
			src_unit = sw2hw[sw_stage]
			dst_unit = sw2hw[output_stage]
			print(src_unit, dst_unit)
			if check_buffer_consistency(src_unit, dst_unit):
				print("[edge]", src_unit, dst_unit, sw_stage, output_stage)
				buffer_edge_dict[src_unit, dst_unit] = src_unit.output_buffer
				dst_unit.set_input_hw_unit(sw_stage, src_unit)

	return buffer_edge_dict

'''
	Allocate actual buffer for each producer-consumer pair, this function is used to
	check the progress of each compute stage and perform sanity check after each computation.
'''
def allocate_output_buffer(sw_stages, hw2sw, sw2hw, buffer_edge_dict):
	src_stages = []
	for sw_stage in sw_stages:
		for in_stage in sw_stage.input_stages:
			# find producer and consumer HW.
			src_unit = sw2hw[in_stage]
			dst_unit = sw2hw[sw_stage]
			# find buffer.
			buffer = buffer_edge_dict[src_unit, dst_unit]
			print("buffer", buffer)
			print("reserve_buffer: ", src_unit, dst_unit, in_stage)
			# allocate a buffer size as the same size of the output dimension.
			buffer.reserve_buffer(
				src_hw_unit = src_unit, 
				dst_hw_unit = dst_unit, 
				sw_stage = in_stage,
				buffer_size = in_stage.output_size
			)
			# append input stage to the src_stage list. This will be used to find the final stage.
			# Final stage: only serves as producer and no corresponding consumer HW unit.
			if in_stage not in src_stages:
				src_stages.append(in_stage)

	# allocate buffer for the final stage.
	for sw_stage in sw_stages:
		# this means that the sw stage is the last stage in the pipeline
		if sw_stage not in src_stages:
			src_unit = sw2hw[sw_stage]
			buffer = src_unit.output_buffer

			buffer.reserve_solo_buffer(
				src_hw_unit = src_unit, 
				sw_stage = sw_stage, 
				buffer_size = sw_stage.output_size
			)

'''
	This function is used to calculate the next index for both input buffer and output buffer.
'''
def increment_buffer_index(buffer_index, buffer_size, throughput):
	new_buffer_index = np.zeros_like(buffer_index)
	if len(buffer_index) == 3:
		if throughput[0] + buffer_index[0] < buffer_size[0]:
			new_buffer_index[0] = throughput[0] + buffer_index[0]
			new_buffer_index[1] = buffer_index[1]
			new_buffer_index[2] = buffer_index[2]
		elif throughput[1] + buffer_index[1] < buffer_size[1]:
			new_buffer_index[1] = throughput[1] + buffer_index[1]
			new_buffer_index[0] = 0
			new_buffer_index[2] = buffer_index[2]
		elif throughput[2] + buffer_index[2] < buffer_size[2]:
			new_buffer_index[2] = throughput[2] + buffer_index[2]
			new_buffer_index[0] = 0
			new_buffer_index[1] = 0
		else:
			new_buffer_index[0] = buffer_size[0]		
			new_buffer_index[1] = buffer_size[1]
			new_buffer_index[2] = buffer_size[2]

	else:
		raise Exception("Fail to increment buffer index, buffer index size needs to be 3.")

	return new_buffer_index

'''
	This function check if one sw stage finishes writing the output.
	If finish, return true, otherwise, return false
'''
def check_stage_finish(src_hw_unit, sw_stage, hw2sw):
	# get the output buffer index
	src_index = src_hw_unit.get_output_buffer_index(sw_stage)
	# find the output buffer, any sw_stage points to the same output buffer
	src_output_buffer = src_hw_unit.output_buffer

	# get the output buffer size
	output_buffer = src_output_buffer.reserved_buffer[src_hw_unit, sw_stage]
	output_buffer_shape = output_buffer.shape

	if len(output_buffer_shape) != len(src_index):
		raise Exception("the dimensions of Buffer size and source index are not matched.")
	else:
		num_element = 1
		for i in range(len(output_buffer_shape)):
			num_element = num_element * output_buffer_shape[i]
			if output_buffer_shape[i] != src_index[i]:
				return False

		sum_val = np.sum(output_buffer)
		if sum_val != num_element:
			print(np.where(output_buffer == 0))
			raise Exception("output buffer is not filled correctly!")

		return True

'''
	To calculate the next index to access. The access pattern is row-major.
	This function takes care of carrying, e.g. x+i exceeds the x dimension.
	src_index: the base index (x, y, z).
	i: the increment amount in x-axis.
	j: the increment amount in y-axis.
	k: the increment amount in z-axis.
'''
def calc_index(src_index, buffer_shape, i, j, k):
	x = src_index[0] + i
	carry = 0
	if x >= buffer_shape[0]:
		carry = 1
		x = x - buffer_shape[0]

	y = src_index[1] + carry + j
	carry = 0
	if y >= buffer_shape[1]:
		carry = 1
		y = y - buffer_shape[1]

	z = src_index[2] + carry + k
	if z >= buffer_shape[2]:
		print(
			"WARNING: [%d:%d:%d] is out of buffer size [%d:%d:%d]." % \
			(x, y, z, buffer_shape[0], buffer_shape[1], buffer_shape[2])
		)

	return x, y, z
'''
	write data to the output buffer, before call this funtion,
	make sure check if the input data for the source hw is ready.
'''
def write_output_throughput(src_hw_unit, sw_stage, hw2sw):
	# find the output buffer, any sw_stage points to the same output buffer
	src_output_buffer = src_hw_unit.output_buffer

	
	print(
		"[write_output_throughput]", 
		sw_stage, 
		src_output_buffer.reserved_buffer[src_hw_unit, sw_stage].shape
	)
	# find the reserved buffer and buffer index
	src_index = src_hw_unit.get_output_buffer_index(sw_stage)
	src_output_throughput = src_hw_unit.output_throughput
	output_buffer = src_output_buffer.reserved_buffer[src_hw_unit, sw_stage]
	output_buffer_shape = output_buffer.shape
	print(
		"[write_output_throughput]", sw_stage, 
		"src_output_throughput:", src_output_throughput, 
		"src_index:", src_index,
		"output_buffer_shape:", output_buffer_shape
	)
	# mark each output element in the output buffer. Change value from 0 to 1
	if len(src_output_throughput) == 3:
		for i in range(src_output_throughput[0]):
			for j in range(src_output_throughput[1]):
				for k in range(src_output_throughput[2]):
					x, y, z = calc_index(src_index, output_buffer_shape, i, j, k)
					# ignore the index out of bound.
					if x < output_buffer_shape[0] and y < output_buffer_shape[1] and z < output_buffer_shape[2]:
						output_buffer[x, y, z] = 1
	else:
		raise Exception("Non-implementation Error, throughput shape size needs to be 3.")

	# this finds the new buffer index for next compute.
	new_buffer_index = increment_buffer_index(src_index, output_buffer_shape, src_output_throughput)
	print(
		"[write_output_throughput]", "src_index: ", src_index, 
		"new_src_index: ", new_buffer_index, 
		"src_output_throughput: ", src_output_throughput
	)
	# set the new buffer index.
	src_hw_unit.set_output_buffer_index(sw_stage, new_buffer_index)

'''
	This function is used to check if the input buffer has enough data to be consumed
	by the consumer unit.
	e.g. for a 3x3 Conv ops. it checks that if there is a new batch of 3x3 data in input buffer.
'''
def check_input_buffer_data_ready(dst_input_buffer, dst_input_throughput, dst_input_index):
	if len(dst_input_throughput) == 3:
		sum_val = np.sum(
			dst_input_buffer[
				dst_input_index[0]:dst_input_index[0]+dst_input_throughput[0],
				dst_input_index[1]:dst_input_index[1]+dst_input_throughput[1],
				dst_input_index[2]:dst_input_index[2]+dst_input_throughput[2],
			]
		)
		print("[check_input_buffer_data_ready] [dst_input_curr_index : +input throughput] --> [", 
			  dst_input_index[0], ":", dst_input_index[0]+dst_input_throughput[0], ",",
			  dst_input_index[1], ":", dst_input_index[1]+dst_input_throughput[1], ",",
			  dst_input_index[2], ":", dst_input_index[2]+dst_input_throughput[2], "]")
		if sum_val == dst_input_throughput[0]*dst_input_throughput[1]*dst_input_throughput[2]:
			return True
		else:
			return False

	else:
		raise Exception("check_input_buffer_data_ready hasn't been implemented throughput other than 3 yet!")
'''
	increment the input buffer index, the input buffer index needs to be incremented before fetching
	the next batch of data.
'''
def increment_input_buffer_index(dst_hw_unit, sw_stage):
	# in this case, no producer dependency, return directly
	# no need to increment the input buffer index
	if dst_hw_unit.input_buffer is None:
		return

	dst_input_buffer = dst_hw_unit.input_buffer
	# print(dst_hw_unit, "has %d dependencies." % len(dst_hw_unit.input_throughput))
	# print("# ", dst_hw_unit, dst_hw_unit.input_hw_units)
	# print("input_throughput size", dst_hw_unit.input_throughput)
	# print(dst_hw_unit.input_index_list, sw_stage.input_stages)

	# needs to increment index for each input throughput
	for i in range(len(dst_hw_unit.input_throughput)):
		input_sw_stage = sw_stage.input_stages[i]
		# 0 here is to find the first one item in the list,
		# the list is a length of 1 list.
		src_hw_unit = dst_hw_unit.input_hw_units[input_sw_stage][0]

		dst_input_buffer = dst_hw_unit.input_buffer.reserved_buffer[src_hw_unit, input_sw_stage]
		dst_input_throughput = dst_hw_unit.input_throughput[i]
		# get the previous input index
		dst_input_index = dst_hw_unit.get_input_buffer_index(src_hw_unit, input_sw_stage)
		# increment the input buffer index
		new_dst_input_index = increment_buffer_index(dst_input_index, dst_input_buffer.shape, dst_input_throughput)
		# set the new index
		dst_hw_unit.set_input_buffer_index(src_hw_unit, input_sw_stage, new_dst_input_index)
	return

'''
	Check for this particular SW stage, if the input data are ready.	
'''
def check_input_buffer(dst_hw_unit, sw_stage):
	# in this case, no producer dependency, return true directly
	if dst_hw_unit.input_buffer is None:
		print("[check_input_buffer]", dst_hw_unit, "has no dependencies and is ready")
		return True

	dst_input_buffer = dst_hw_unit.input_buffer
	print("[check_input_buffer]", dst_hw_unit, "has %d dependencies." % len(dst_hw_unit.input_throughput))
	print("[check_input_buffer]", dst_hw_unit, dst_hw_unit.input_hw_units)
	# print("input_throughput size", dst_hw_unit.input_throughput)
	print("[check_input_buffer]", dst_hw_unit.input_index_list, sw_stage.input_stages)
	for i in range(len(dst_hw_unit.input_throughput)):
		input_sw_stage = sw_stage.input_stages[i]
		src_hw_unit = dst_hw_unit.input_hw_units[input_sw_stage][0]
		dst_input_buffer = dst_hw_unit.input_buffer.reserved_buffer[src_hw_unit, input_sw_stage]
		dst_input_throughput = dst_hw_unit.input_throughput[i]
		dst_input_index = dst_hw_unit.input_index_list[src_hw_unit, input_sw_stage]

		if not check_input_buffer_data_ready(dst_input_buffer, dst_input_throughput, dst_input_index):
			print("[check_input_buffer]", dst_hw_unit, "-> input sw_stage: ", input_sw_stage, "not ready")
			return False

		print("[check_input_buffer]", dst_hw_unit, ", input sw_stage: ", input_sw_stage, "ready")

	return True
