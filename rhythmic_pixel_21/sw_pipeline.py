
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

	comp_stage = ProcessStage(
		name = "MaskComp",
		input_size = [(1280, 720, 3)],
		kernel_size = [(4, 1, 3)],
		stride = [(4, 1, 1)],
		output_size = (320, 720, 1),
		padding = [Padding.NONE],
	)
	sw_stage_list.append(comp_stage)

	sampler_stage = ProcessStage(
		name = "Sampler",
		input_size = [(1280, 720, 3)],
		kernel_size = [(2, 1, 1)],
		stride = [(2, 1, 1)],
		output_size = (640, 720, 3),
		padding = [Padding.NONE]
	)
	sw_stage_list.append(sampler_stage)

	input_data = PixelInput((1280, 720, 3), name="Input")
	sw_stage_list.append(input_data)

	comp_stage.set_input_stage(input_data)
	sampler_stage.set_input_stage(input_data)

	return sw_stage_list

if __name__ == '__main__':

	sw_stage_list = sw_pipeline()
	build_sw_graph(sw_stage_list)







