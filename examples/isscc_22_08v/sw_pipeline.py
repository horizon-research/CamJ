
import path
import sys
import os
  
# directory reach
parent_directory = os.path.dirname(os.getcwd())
# setting path
sys.path.append(os.path.dirname(parent_directory))

from camj.sim_core.sw_interface import ProcessStage, DNNProcessStage, PixelInput
from camj.sim_core.sw_utils import build_sw_graph

def sw_pipeline():

	sw_stage_list = []
	conv_stage = ProcessStage(
		name = "Conv",
		input_size = [(126, 126, 1)],
        kernel_size = [(3, 3, 1)],
        num_kernels = [1],
        stride = [(3, 3, 1)],
		output_size = (42, 42, 1),
        padding = [False]
	)
	sw_stage_list.append(conv_stage)

	mp_stage = ProcessStage(
		name = "MaxPool",
		input_size = [(42, 42, 1)],
        kernel_size = [(2, 2, 1)],
        num_kernels = [1],
        stride = [(2, 2, 1)],
		output_size = (21, 21, 1),
        padding = [False]
	)
	sw_stage_list.append(mp_stage)

	input_data = PixelInput((126, 126, 1), name="Input")
	sw_stage_list.append(input_data)

	conv_stage.set_input_stage(input_data)
	
	mp_stage.set_input_stage(conv_stage)

	return sw_stage_list

if __name__ == '__main__':

	sw_stage_list = sw_pipeline()
	build_sw_graph(sw_stage_list)







