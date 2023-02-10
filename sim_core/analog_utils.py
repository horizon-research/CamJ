import numpy as np
from sim_core.analog_infra import AnalogArray, AnalogComponent
from sim_core.enum_const import ProcessDomain


def check_component_internal_connect_consistency(analog_component):
	# if there is no component or one component inside the analog component,
	# no need to check the consistency
	if len(analog_component.components) <= 1:
		return True

	head_list = analog_component.source_component
	new_head_list = []

	while len(head_list) > 0:
		for component in head_list:
			for output_component in component.output_component:
				if component.output_domain not in output_component.input_domain:
					raise Exception("Internal connection consistency failed. Domain mismatch.")

				if output_component not in new_head_list:
					new_head_list.append(output_component)

		print(head_list)
		head_list = new_head_list
		new_head_list = []


def check_array_internal_connect_consistency(analog_array):
	# first check the correctness of every component internal connection
	for analog_component in analog_array.components:
		check_component_internal_connect_consistency(analog_component)

	# then check the correctness of inter-component internal connection
	head_list = analog_array.source_components
	new_head_list = []
	while len(head_list) > 0:
		for component in head_list:
			for output_component in component.output_components:
				if component.output_domain not in output_component.input_domain:
					raise Exception("Internal connection consistency failed. Domain mismatch.")

				if output_component not in new_head_list:
					new_head_list.append(output_component)

		head_list = new_head_list
		new_head_list = []

def find_head_analog_array(analog_arrays):
	head_analog_arrays = []
	for analog_array in analog_arrays:
		if len(analog_array.input_arrays) == 0:
			head_analog_arrays.append(analog_array)

	return head_analog_arrays

def check_input_output_requirement_consistency(analog_array):
	refined_input_domain = []
	for domain in analog_array.input_domain:
		if domain != ProcessDomain.OPTICAL:
			refined_input_domain.append(domain)

	print(refined_input_domain, analog_array.input_arrays)
	if len(refined_input_domain) != len(analog_array.input_arrays):
		raise Exception("Analog array: '%s' input domain size is not equal to its input_array size" % analog_array.name)


def check_analog_connect_consistency(analog_arrays):
	for analog_array in analog_arrays:
		check_array_internal_connect_consistency(analog_array)

	head_analog_arrays = find_head_analog_array(analog_arrays)
	new_head_analog_arrays = []
	while len(head_analog_arrays) > 0:
		for analog_array in head_analog_arrays:
			check_input_output_requirement_consistency(analog_array)
			for output_array in analog_array.output_arrays:
				print(analog_array.name, output_array.name)
				if analog_array.output_domain not in output_array.input_domain:
					raise Exception("Internal connection consistency failed. Domain mismatch.")

				if output_array not in new_head_analog_arrays:
					new_head_analog_arrays.append(output_array)

		head_analog_arrays = new_head_analog_arrays
		new_head_analog_arrays = []

def reverse_sw_to_analog_mapping(analog_arrays, analog_sw_stages, mapping_dict):
	analog_to_sw = {}
	analog_dict = {}

	for analog_array in analog_arrays:
		analog_dict[analog_array.name] = analog_array

	for sw_stage in analog_sw_stages:
		analog_array = analog_dict[mapping_dict[sw_stage.name]]
		if mapping_dict[sw_stage.name] in analog_to_sw:
			analog_to_sw[analog_array].append(sw_stage)
		else:
			analog_to_sw[analog_array] = [sw_stage]

	return analog_to_sw

def count_sw_mapping_dependency(sw_stages):
	visited = []
	cnt = 0

	for sw_stage in sw_stages:
		curr_list = [sw_stage]
		new_list = []
		if sw_stage not in visited:
			cnt += 1
			while len(curr_list) > 0:
				for input_stage in sw_stage.input_stages:
					if input_stage not in visited:
						visited.append(input_stage)
						if input_stage not in new_list:
							new_list.append(input_stage)

				for output_stage in sw_stage.output_stages:
					if output_stage not in visited:
						visited.append(output_stage)
						if output_stage not in new_list:
							new_list.append(output_stage)

				curr_list = new_list
				new_list = []

	return cnt


def compute_total_energy(analog_arrays, analog_sw_stages, mapping_dict):
	
	analog_to_sw = reverse_sw_to_analog_mapping(analog_arrays, analog_sw_stages, mapping_dict)

	total_energy = 0
	for analog_array in analog_to_sw.keys():
		# check data dependency
		cnt = count_sw_mapping_dependency(analog_to_sw[analog_array])
		print(analog_array, cnt)
		total_energy += cnt * analog_array.energy()

	return total_energy

def check_analog_pipeline(analog_arrays):

	head_analog_arrays = find_head_analog_array(analog_arrays)
	finished_analog_arrays = []
	new_head_analog_arrays = []
	idx = 1
	while len(head_analog_arrays) > 0:
		print("[Pipeline stage %d]" % idx)
		idx += 1
		readiness = True

		# check if this analog array's dependencies are ready
		for analog_array in head_analog_arrays:
			for input_array in analog_array.input_arrays:
				if input_array not in finished_analog_arrays:
					readiness = False

			if not readiness:
				# add back to next iteration
				new_head_analog_arrays.append(analog_array)
				continue

			print("Process", analog_array)
			finished_analog_arrays.append(analog_array)
			for output_array in analog_array.output_arrays:
				print(analog_array.name, "-->", output_array.name)
				if output_array not in new_head_analog_arrays:
					new_head_analog_arrays.append(output_array)

		head_analog_arrays = new_head_analog_arrays
		new_head_analog_arrays = []

def find_analog_sw_stages(sw_stages, analog_arrays, mapping_dict):
	analog_sw_stages = []

	for sw_stage in sw_stages:
		hw_stage_name = mapping_dict[sw_stage.name]

		for analog_array in analog_arrays:
			if analog_array.name == hw_stage_name:
				analog_sw_stages.append(sw_stage)
				break

	return analog_sw_stages

def launch_analog_simulation(analog_arrays, sw_stages, mapping_dict):
	# check analog connection correctness
	check_analog_connect_consistency(analog_arrays)
	# find stages corresponding to analog computing
	analog_sw_stages = find_analog_sw_stages(sw_stages, analog_arrays, mapping_dict)
	# check analog pipeline correctness
	check_analog_pipeline(analog_arrays)
	# compute analog computing energy
	total_energy = compute_total_energy(analog_arrays, analog_sw_stages, mapping_dict)
	
	return total_energy


	