from pprint import pprint
import numpy as np


# import local modules
from enum_const import ProcessorLocation, ProcessDomain
from memory import Scratchpad
from hw_compute import ADC, ComputeUnit, SystolicArray, NeuralProcessor
from sim_utils import map_sw_hw, check_buffer_consistency, build_buffer_edges, allocate_output_buffer, \
					  increment_buffer_index, check_stage_finish, write_output_throughput, \
					  check_input_buffer_data_ready, increment_input_buffer_index, check_input_buffer, \
					  check_finish_data_dependency, check_fc_input_ready, check_input_stage_finish
from sim_infra import ReservationBoard, BufferMonitor
from sw_framework_interface import build_sw_graph
from flags import *

# from isscc_22_08v.mapping_file import mapping_function
# from isscc_22_08v.sw_pipeline import sw_pipeline
# from isscc_22_08v.hw_config import hw_config

from ieee_vr22.mapping_file import mapping_function
from ieee_vr22.sw_pipeline import sw_pipeline
from ieee_vr22.hw_config import hw_config

# from isscc_16_1_42.mapping_file import mapping_function
# from isscc_16_1_42.sw_pipeline import sw_pipeline
# from isscc_16_1_42.hw_config import hw_config

# from isscc_17_0_62.mapping_file import mapping_function
# from isscc_17_0_62.sw_pipeline import sw_pipeline
# from isscc_17_0_62.hw_config import hw_config

# from isscc_08_iVisual.mapping_file import mapping_function
# from isscc_08_iVisual.sw_pipeline import sw_pipeline
# from isscc_08_iVisual.hw_config import hw_config

# from isscc_13_reconfigurable.mapping_file import mapping_function
# from isscc_13_reconfigurable.sw_pipeline import sw_pipeline
# from isscc_13_reconfigurable.hw_config import hw_config

# from isscc_21_back_illuminated.mapping_file import mapping_function
# from isscc_21_back_illuminated.sw_pipeline import sw_pipeline
# from isscc_21_back_illuminated.hw_config import hw_config

# from rhythmic_pixel_21.mapping_file import mapping_function
# from rhythmic_pixel_21.sw_pipeline import sw_pipeline
# from rhythmic_pixel_21.hw_config import hw_config

# from simple_img_pipeline.mapping_file import mapping_function
# from simple_img_pipeline.sw_pipeline import sw_pipeline
# from simple_img_pipeline.hw_config import hw_config

# from simple_systolic_array.mapping_file import mapping_function
# from simple_systolic_array.sw_pipeline import sw_pipeline
# from simple_systolic_array.hw_config import hw_config

def main():
	hw_dict = hw_config()
	mapping_dict = mapping_function()
	sw_stage_list = sw_pipeline()
	reservation_board = ReservationBoard(hw_dict["compute"])
	buffer_monitor = BufferMonitor(hw_dict["memory"])

	build_sw_graph(sw_stage_list)

	sw2hw, hw2sw = map_sw_hw(mapping_dict, sw_stage_list, hw_dict)

	print("## [sw2hw] ##")
	pprint(sw2hw)

	print("## [hw2sw] ##")
	pprint(hw2sw)

	buffer_edge_dict = build_buffer_edges(sw_stage_list, hw_dict, sw2hw)

	# print(buffer_edge_dict)

	allocate_output_buffer(
		sw_stages = sw_stage_list,
		hw2sw = hw2sw, 
		sw2hw = sw2hw, 
		buffer_edge_dict = buffer_edge_dict
	)
	# exit()

	# # to check the correctness of the implementation
	# for sw_stage in sw_stage_list:
	# 	hw_stage = sw2hw[sw_stage]
	# 	print("[src hw stages]: ", hw_stage, sw_stage)
	# 	# pprint(hw_stage.input_hw_units)
	# 	pprint(hw_stage.output_buffer_size)
	# 	# pprint(hw_stage.output_index_list)

	# initialize different stage list
	idle_stage = {}
	writing_stage = {}
	reading_stage = {}
	processing_stage = {}
	finished_stage = {}
	reserved_cycle_cnt = {}
	
	# initialize every stage to idle stage
	for sw_stage in sw_stage_list:
		idle_stage[sw_stage] = True

	for cycle in range(3500000):
		if cycle % PRINT_CYCLE == 0:
			print("\n\n#######  CYCLE %04d  ######" % cycle)
		# always refresh the R/W port status first,
		# otherwise, it won't release the port free.
		buffer_monitor.refresh_port_status()

		# iterate each sw_stage
		for sw_stage in sw_stage_list:
			hw_unit = sw2hw[sw_stage]
			if cycle % PRINT_CYCLE == 0:
				print("[ITERATE] HW: ", hw_unit, ", SW: ", sw_stage)

			if sw_stage in finished_stage:
				if cycle % PRINT_CYCLE == 0:
					print("[FINISH]", sw_stage, "is finished already")
				continue

			if sw_stage in reserved_cycle_cnt:
				reserved_cycle_cnt[sw_stage] += 1

			# This check the writing stage. 
			# First, check if there is any data to write,
			# Second, check if there is any avialble ports in current cycle, 
			# if yes, request port and write data.
			if sw_stage in writing_stage:
				if cycle % PRINT_CYCLE == 0:
					print("[WRITE]", sw_stage, "in writing stage")
				output_buffer = hw_unit.output_buffer
				remain_write_cnt = hw_unit.num_write_remain()
				if cycle % PRINT_CYCLE == 0:
					print("[WRITE]", "[HW unit : SW stage]", hw_unit, sw_stage, "Output Buffer: ", output_buffer)
				# this means that this hw_unit doesn't have any output data.
				if remain_write_cnt == 0:
					if cycle % PRINT_CYCLE == 0:
						print("[WRITE]", hw_unit, "has no output data.")
					# set sw_stage to idle stage
					idle_stage[sw_stage] = True
					writing_stage.pop(sw_stage)

				# check if there is some write port available
				elif buffer_monitor.check_buffer_available_write_port(output_buffer):
					# request write port, it returns the current available write port
					num_avail_write_port = buffer_monitor.request_write_port(output_buffer, remain_write_cnt)

					# then, check if there is any space to write
					if output_buffer.have_space_to_write(num_avail_write_port):
						output_buffer.write_data(num_avail_write_port)
						# if number of available ports is greater than 0,
						# then log the aoumd of read data, else, avoid logging
						if num_avail_write_port > 0:
							write_index = hw_unit.write_to_output_buffer(num_avail_write_port)
							# output data to the targeted buffer and increment output buffer index
							write_output_throughput(hw_unit, sw_stage, hw2sw, write_index, num_avail_write_port)
							if hw_unit.check_write_finish():
								if cycle % PRINT_CYCLE == 0:
									print("[WRITE]", hw_unit, "finishes writing")
								# set sw_stage to idle stage
								idle_stage[sw_stage] = True
								writing_stage.pop(sw_stage)
					else:
						if cycle % PRINT_CYCLE == 0:
							print("[WRITE]", output_buffer, "have no space to write")


				if check_stage_finish(hw_unit, sw_stage, hw2sw):
					if cycle % PRINT_CYCLE == 0:
						print("[WRITE]", sw_stage, "finish writing the buffer.", hw_unit, "is released.")
					reservation_board.release_hw_unit(sw_stage, hw_unit)
					finished_stage[sw_stage] = True
					# also need to pop sw_stage from the idle stage
					idle_stage.pop(sw_stage)
					# check if all input stages of sw_stage have been finished,
					# this is used to check if there is data dependency is correct
					check_finish_data_dependency(sw_stage, finished_stage)


			# this will check if a sw stage is already into computing phase,
			# wait for the compute to be finished
			if sw_stage in processing_stage:
				if cycle % PRINT_CYCLE == 0:
					print("[PROCESS]", sw_stage, "in processing_stage")
				hw_unit.process_one_cycle()
				# check_input_buffer(hw_unit, sw_stage)
				if hw_unit.finish_computation():
					# # output data to the targeted buffer and increment output buffer index
					# write_output_throughput(hw_unit, sw_stage, hw2sw)

					# if the computation is finished, remove the sw stage from processing stage list
					# add sw_stage to writing stage
					writing_stage[sw_stage] = True
					processing_stage.pop(sw_stage)

			# check if the sw stage is in reading phase
			elif sw_stage in reading_stage:
				if cycle % PRINT_CYCLE == 0:
					print("[READ]", sw_stage, "in reading stage")
				# find input buffer and remaining amount of data need to be read
				input_buffer = hw_unit.input_buffer
				remain_read_cnt = hw_unit.num_read_remain()
				if cycle % PRINT_CYCLE == 0:
					print("[READ]", "[HW unit : SW stage]", hw_unit, sw_stage, "Input Buffer: ", input_buffer)
				# this means that this hw_unit doesn't have data dependencies.
				if remain_read_cnt == 0:
					if cycle % PRINT_CYCLE == 0:
						print("[READ]", hw_unit, "is ready to compute, no data dependencies")
					# refresh the compute status in hw_unit
					hw_unit.init_elapse_cycle()
					processing_stage[sw_stage] = True
					reading_stage.pop(sw_stage)

				# check if there is some read port available
				elif buffer_monitor.check_buffer_available_read_port(input_buffer):
					# request read port, it returns the current available read port
					num_avail_read_port = buffer_monitor.request_read_port(input_buffer, remain_read_cnt)

					# check if there is any data can be read from buffer
					if input_buffer.have_data_read(num_avail_read_port):
						input_buffer.read_data(num_avail_read_port)
						# if number of available ports is greater than 0,
						# then log the aoumd of read data, else, avoid logging
						if num_avail_read_port > 0:
							hw_unit.read_from_input_buffer(num_avail_read_port)
							if hw_unit.check_read_finish():
								if cycle % PRINT_CYCLE == 0:
									print("[READ]", hw_unit, "is ready to compute")
								# refresh the compute status in hw_unit
								hw_unit.init_elapse_cycle()
								processing_stage[sw_stage] = True
								reading_stage.pop(sw_stage)
					# here to check if all input stages are finished, if so, this stage uses zero paddings
					elif check_input_stage_finish(sw_stage, finished_stage):
						if num_avail_read_port > 0:
							hw_unit.read_from_input_buffer(num_avail_read_port)
							if hw_unit.check_read_finish():
								if cycle % PRINT_CYCLE == 0:
									print("[READ]", hw_unit, "is ready to compute")
								# refresh the compute status in hw_unit
								hw_unit.init_elapse_cycle()
								processing_stage[sw_stage] = True
								reading_stage.pop(sw_stage)
					else:
						if cycle % PRINT_CYCLE == 0:
							print("READ", input_buffer, "input_buffer have no new data to read")

			# check if the sw stage is in idle phase
			elif sw_stage in idle_stage:
				# this check is to help to config the systolic array into correct configuration
				# before checking the data readiness.
				# Otherwise, there can be some infinite checkings in the program due to incorrect
				# systolic array configuration.
				if not reservation_board.check_reservation(hw_unit):
					# check if the hw unit is a systolic array instance,
					# if yes, needs to modify the input/output throughput.
					if isinstance(hw_unit, SystolicArray):
						hw_unit.config_throughput(
							sw_stage.ifmap_size, 
							sw_stage.output_size,
							sw_stage.stride[0][0],
							sw_stage.kernel_size[0][0],
							sw_stage.op_type
						)
					# same for neural processor instance
					elif isinstance(hw_unit, NeuralProcessor):
						hw_unit.config_throughput(
							sw_stage.ifmap_size, 
							sw_stage.output_size,
							sw_stage.stride[0][0],
							sw_stage.kernel_size[0][0],
							sw_stage.op_type
						)

				# first to check if the input buffer contains the data
				if check_input_buffer(hw_unit, sw_stage) or check_fc_input_ready(sw_stage, finished_stage):
					if cycle % PRINT_CYCLE == 0:
						print("[IDLE]", sw_stage, "in idle stage, input data ready")
					# if the hw unit is not occupied by any sw stage, reserve the hw unit
					if not reservation_board.check_reservation(hw_unit):
						if cycle % PRINT_CYCLE == 0:
							print("[IDLE]", sw_stage, "request --> HW: ", hw_unit, "is available.")
						# reserve the hw unit first
						reservation_board.reserve_hw_unit(sw_stage, hw_unit)
						reserved_cycle_cnt[sw_stage] = 0
						
						hw_unit.start_init_delay()
						# increment the input buffer index
						increment_input_buffer_index(hw_unit, sw_stage)
						# exit()
						# hw_unit.init_elapse_cycle()
						reading_stage[sw_stage] = True
						idle_stage.pop(sw_stage)
					elif reservation_board.reserve_by(sw_stage, hw_unit):
						# increment the input buffer index
						increment_input_buffer_index(hw_unit, sw_stage)
						# hw_unit.init_elapse_cycle()
						reading_stage[sw_stage] = True
						idle_stage.pop(sw_stage)
					else:
						if cycle % PRINT_CYCLE == 0:
							print("[IDLE] HW: ", hw_unit, "is not available.")
				else:
					if cycle % PRINT_CYCLE == 0:
						print("[IDLE]", sw_stage, "in idle stage, input data NOT ready")

		if cycle % PRINT_CYCLE == 0:				
			print("[Finished stage]: ", finished_stage)


		if len(finished_stage.keys()) == len(sw_stage_list):
			hw_list = hw_dict["compute"]
			print("Overall system cycle count: ", cycle)
			print("[Cycle distribution]", reserved_cycle_cnt)
			for hw_unit in hw_list:
				print(hw_unit, 
					"total_cycle: ", hw_unit.sys_all_compute_cycle, 
					"total_write: ", hw_unit.sys_all_write_cnt,
					"total_read: ", hw_unit.sys_all_read_cnt,
					"total_compute_energy: %d pJ" % hw_unit.compute_energy(),
					"total_comm_energy: %d pJ" % hw_unit.communication_energy())
			print("DONE!")
			exit()

if __name__ == '__main__':
	main()
