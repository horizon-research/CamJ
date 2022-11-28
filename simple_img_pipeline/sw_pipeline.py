
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
		input_size = [(32, 32, 1)],
		kernel_size = [(3, 3, 1)],
		stride = [(1, 1, 1)],
		output_size = (32, 32, 1),
		padding = [Padding.ZEROS]
	)
	sw_stage_list.append(conv1_stage)

	conv2_stage = ProcessStage(
		name = "Conv2",
		input_size = [(32, 32, 1)],
		kernel_size = [(2, 2, 1)],
		stride = [(2, 2, 1)],
		output_size = (16, 16, 1),
		padding = [Padding.NONE]
	)
	sw_stage_list.append(conv2_stage)

	abs_stage = ProcessStage(
		name = "Abs",
		input_size = [(16, 16, 1)],
		kernel_size = [(1, 1, 1)],
		stride = [(1, 1, 1)],
		output_size = (16, 16, 1),
		padding = [Padding.NONE]
	)
	sw_stage_list.append(abs_stage)

	input_data = PixelInput((32, 32, 1), name="Input")
	sw_stage_list.append(input_data)

	conv1_stage.set_input_stage(input_data)
	conv2_stage.set_input_stage(conv1_stage)
	abs_stage.set_input_stage(conv2_stage)

	return sw_stage_list

if __name__ == '__main__':

	sw_stage_list = sw_pipeline()
	build_sw_graph(sw_stage_list)







