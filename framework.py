from pprint import pprint
import numpy as np


# import local modules
from enum_const import ProcessorLocation, ProcessDomain
from memory import Scratchpad
from hw_compute import ADC, ComputeUnit, SystolicArray
from mapping_file import mapping_function
from sw_pipeline import sw_pipeline, build_sw_graph
from sim_utils import map_sw_hw, check_buffer_consistency, build_buffer_edges, allocate_output_buffer, \
					  increment_buffer_index, check_stage_finish, find_index, write_output_throughput, \
					  check_input_buffer_data_ready, increment_input_buffer_index, check_input_buffer

from sim_infra import ReservationBoard
from hw_config import hw_config


def main():
	hw_dict = hw_config()
	mapping_dict = mapping_function()
	sw_stage_list = sw_pipeline()
	reservation_board = ReservationBoard(hw_dict["compute"])

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

	# exit()


	finished_stage = {}
	processing_stage = {}

	for cycle in range(800000):
		print("\n\n#######  CYCLE %04d  ######" % cycle)
		for sw_stage in sw_stage_list:

			hw_unit = sw2hw[sw_stage]
			print("[== HW: ", hw_unit, ", SW: ", sw_stage)

			if sw_stage in finished_stage:
				print(sw_stage, "is finished already")
				continue

			

			# this will check if a sw stage is already into computing phase,
			# wait for the compute to be finished
			if sw_stage in processing_stage:
				hw_unit.process_one_cycle()
				check_input_buffer(hw_unit, sw_stage)
				if hw_unit.finish_computation():
					# output data to the targeted buffer and increment output buffer index
					write_output_throughput(hw_unit, sw_stage, hw2sw)
					# if the computation is finished, remove the sw stage from processing stage list
					processing_stage.pop(sw_stage)
					if check_stage_finish(hw_unit, sw_stage, hw2sw):
						print("## ", sw_stage, "finish writing the buffer.", hw_unit, "is released.")
						reservation_board.release_hw_unit(sw_stage, hw_unit)
						finished_stage[sw_stage] = True
			elif check_input_buffer(hw_unit, sw_stage):
				# if the hw unit is not occupied by any sw stage, reserve the hw unit
				if not reservation_board.check_reservation(hw_unit):
					print("HW: ", hw_unit, "is available.")
					# reserve the hw unit first
					reservation_board.reserve_hw_unit(sw_stage, hw_unit)
					# increment the input buffer index
					increment_input_buffer_index(hw_unit, sw_stage)
					hw_unit.init_elapse_cycle()
					processing_stage[sw_stage] = True
					# # output data to the targeted buffer and increment output buffer index
					# write_output_throughput(hw_unit, sw_stage, hw2sw)
					# if check_stage_finish(hw_unit, sw_stage, hw2sw):
					# 	print("## ", sw_stage, "finish writing the buffer.", hw_unit, "is released.")
					# 	reservation_board.release_hw_unit(sw_stage, hw_unit)
					# 	finished_stage[sw_stage] = True
				elif reservation_board.reserve_by(sw_stage, hw_unit):
					# increment the input buffer index
					increment_input_buffer_index(hw_unit, sw_stage)
					hw_unit.init_elapse_cycle()
					processing_stage[sw_stage] = True
					# # output data to the targeted buffer and increment output buffer index
					# write_output_throughput(hw_unit, sw_stage, hw2sw)
					# if check_stage_finish(hw_unit, sw_stage, hw2sw):
					# 	print("## ", sw_stage, "finish writing the buffer.", hw_unit, "is released.")
					# 	reservation_board.release_hw_unit(sw_stage, hw_unit)
					# 	finished_stage[sw_stage] = True
				else:
					print("HW: ", hw_unit, "is not available.")

		print("[Finished stage]: ", finished_stage)
		if len(finished_stage.keys()) == len(sw_stage_list):
			print("DONE!")
			exit()

if __name__ == '__main__':
	main()
