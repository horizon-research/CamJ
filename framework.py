from pprint import pprint
import numpy as np


# import local modules
from enum_const import ProcessorLocation, ProcessDomain
from memory import Scratchpad
from hw_compute import ADC, ComputeUnit, SystolicArray
from sim_utils import map_sw_hw, check_buffer_consistency, build_buffer_edges, allocate_output_buffer, \
					  increment_buffer_index, check_stage_finish, write_output_throughput, \
					  check_input_buffer_data_ready, increment_input_buffer_index, check_input_buffer
from sim_infra import ReservationBoard, BufferMonitor
from sw_framework_interface import build_sw_graph

from simple_img_pipeline.mapping_file import mapping_function
from simple_img_pipeline.sw_pipeline import sw_pipeline, build_sw_graph
from simple_img_pipeline.hw_config import hw_config


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

	print(buffer_edge_dict)

	allocate_output_buffer(
		sw_stages = sw_stage_list,
		hw2sw = hw2sw, 
		sw2hw = sw2hw, 
		buffer_edge_dict = buffer_edge_dict
	)

	# to check the correctness of the implementation
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
	
	# initialize every stage to idle stage
	for sw_stage in sw_stage_list:
		idle_stage[sw_stage] = True

	for cycle in range(40000):
		print("\n\n#######  CYCLE %04d  ######" % cycle)
		# always refresh the R/W port status first,
		# otherwise, it won't release the port free.
		buffer_monitor.refresh_port_status()

		# iterate each sw_stage
		for sw_stage in sw_stage_list:
			hw_unit = sw2hw[sw_stage]
			print("[ITERATE] HW: ", hw_unit, ", SW: ", sw_stage)

			if sw_stage in finished_stage:
				print("[FINISH]", sw_stage, "is finished already")
				continue

			# This check the writing stage. 
			# First, check if there is any data to write,
			# Second, check if there is any avialble ports in current cycle, 
			# if yes, request port and write data.
			if sw_stage in writing_stage:
				print("[WRITE]", sw_stage, "in writing stage")
				output_buffer = hw_unit.output_buffer
				remain_write_cnt = hw_unit.num_write_remain()
				print("[WRITE]", "[HW unit : SW stage]", hw_unit, sw_stage, "Output Buffer: ", output_buffer)
				# this means that this hw_unit doesn't have any output data.
				if remain_write_cnt == 0:
					print("[WRITE]", hw_unit, "has no output data.")
					# set sw_stage to idle stage
					idle_stage[sw_stage] = True
					writing_stage.pop(sw_stage)

				# check if there is some write port available
				elif buffer_monitor.check_buffer_available_write_port(output_buffer):
					# request write port, it returns the current available write port
					num_avail_write_port = buffer_monitor.request_write_port(output_buffer, remain_write_cnt)
					# print(output_buffer, num_avail_write_port)

					# then, check if there is any space to write
					if output_buffer.have_space_to_write(num_avail_write_port):
						output_buffer.write_data(num_avail_write_port)
						# if number of available ports is greater than 0,
						# then log the aoumd of read data, else, avoid logging
						if num_avail_write_port > 0:
							hw_unit.write_to_output_buffer(num_avail_write_port)
							if hw_unit.check_write_finish():
								print("[WRITE]", hw_unit, "finishes writing")
								# output data to the targeted buffer and increment output buffer index
								write_output_throughput(hw_unit, sw_stage, hw2sw)
								# set sw_stage to idle stage
								idle_stage[sw_stage] = True
								writing_stage.pop(sw_stage)
					else:
						print("[WRITE]", output_buffer, "have no space to write")


				if check_stage_finish(hw_unit, sw_stage, hw2sw):
					print("[WRITE]", sw_stage, "finish writing the buffer.", hw_unit, "is released.")
					reservation_board.release_hw_unit(sw_stage, hw_unit)
					finished_stage[sw_stage] = True
					idle_stage.pop(sw_stage)


			# this will check if a sw stage is already into computing phase,
			# wait for the compute to be finished
			if sw_stage in processing_stage:
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
				print("[READ]", sw_stage, "in reading stage")
				# find input buffer and remaining amount of data need to be read
				input_buffer = hw_unit.input_buffer
				remain_read_cnt = hw_unit.num_read_remain()
				print("[READ]", "[HW unit : SW stage]", hw_unit, sw_stage, "Input Buffer: ", input_buffer)
				# this means that this hw_unit doesn't have data dependencies.
				if remain_read_cnt == 0:
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
								print("[READ]", hw_unit, "is ready to compute")
								# refresh the compute status in hw_unit
								hw_unit.init_elapse_cycle()
								processing_stage[sw_stage] = True
								reading_stage.pop(sw_stage)
					else:
						print("READ", input_buffer, "input_buffer have no new data to read")

			# check if the sw stage is in idle phase
			elif sw_stage in idle_stage:
				# first to check if the input buffer contains the data
				if check_input_buffer(hw_unit, sw_stage):
					print("[IDLE]", sw_stage, "in idle stage, input data ready")
					# if the hw unit is not occupied by any sw stage, reserve the hw unit
					if not reservation_board.check_reservation(hw_unit):
						print("[IDLE]", sw_stage, "request --> HW: ", hw_unit, "is available.")
						# reserve the hw unit first
						reservation_board.reserve_hw_unit(sw_stage, hw_unit)
						hw_unit.start_init_delay()
						# increment the input buffer index
						increment_input_buffer_index(hw_unit, sw_stage)
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
						print("[IDLE] HW: ", hw_unit, "is not available.")
				else:
					print("[IDLE]", sw_stage, "in idle stage, input data NOT ready")
		print("[Finished stage]: ", finished_stage)
		if len(finished_stage.keys()) == len(sw_stage_list):
			print("DONE!")
			exit()

if __name__ == '__main__':
	main()
