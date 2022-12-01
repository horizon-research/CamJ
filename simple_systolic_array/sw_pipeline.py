
import path
import sys
import os
  
# directory reach
directory = os.getcwd()
parent_directory = os.path.dirname(directory)
# setting path
sys.path.append(os.path.dirname(directory))
sys.path.append(os.path.dirname(parent_directory))

from enum_const import Padding
from sw_framework_interface import ProcessStage, DNNProcessStage, PixelInput, build_sw_graph

def sw_pipeline():

	sw_stage_list = []
	conv1_stage = ProcessStage(
		name = "Conv1",
		input_size = [(64, 64, 1)],
		kernel_size = [(3, 3, 1)],
		stride = [(1, 1, 1)],
		output_size = (64, 64, 1),
		padding = [Padding.ZEROS]
	)
	sw_stage_list.append(conv1_stage)

	conv2d_1_stage = DNNProcessStage(
		name = "Conv2D_1",
		op_type = "Conv2D",
		ifmap_size = [64, 64, 1],
		kernel_size = [3, 3, 1, 8],
		stride = 2
	)
	sw_stage_list.append(conv2d_1_stage)

	conv2d_2_stage = DNNProcessStage(
		name = "Conv2D_2",
		op_type = "Conv2D",
		ifmap_size = [32, 32, 8],
		kernel_size = [3, 3, 8, 8],
		stride = 2
	)
	sw_stage_list.append(conv2d_2_stage)

	input_data = PixelInput((64, 64, 1), name="Input")
	sw_stage_list.append(input_data)

	conv1_stage.set_input_stage(input_data)
	
	conv2d_1_stage.set_input_stage(conv1_stage)

	conv2d_2_stage.set_input_stage(conv2d_1_stage)

	return sw_stage_list

if __name__ == '__main__':

	sw_stage_list = sw_pipeline()
	build_sw_graph(sw_stage_list)







