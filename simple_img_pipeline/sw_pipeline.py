
import path
import sys
import os
  
# directory reach
directory = os.getcwd()
parent_directory = os.path.dirname(directory)
# setting path
sys.path.append(os.path.dirname(directory))
sys.path.append(os.path.dirname(parent_directory))

from sw_framework_interface import ProcessStage, DNNProcessStage, PixelInput, build_sw_graph

def sw_pipeline():

	sw_stage_list = []
	conv_stage = ProcessStage(
		name = "Conv",
		input_size = [(32, 32, 1)],
		output_size = (30, 30, 1),
		input_reuse = [(1, 3, 1)]
	)
	sw_stage_list.append(conv_stage)

	abs_stage = ProcessStage(
		name = "Abs",
		input_size = [(30, 30, 1)],
		output_size = (30, 30, 1),
		input_reuse = [(1, 1, 1)]
	)
	sw_stage_list.append(abs_stage)

	input_data = PixelInput((32, 32, 1), name="Input")
	sw_stage_list.append(input_data)

	conv_stage.set_input_stage(input_data)
	
	abs_stage.set_input_stage(conv_stage)

	return sw_stage_list

if __name__ == '__main__':

	sw_stage_list = sw_pipeline()
	build_sw_graph(sw_stage_list)







