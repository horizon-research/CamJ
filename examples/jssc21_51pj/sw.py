import sys
import os
  
# directory
parent_directory = os.path.dirname(os.getcwd())
# setting path
sys.path.append(os.path.dirname(parent_directory))

from camj.sim_core.sw_interface import ProcessStage, DNNProcessStage, PixelInput
from camj.sim_core.sw_utils import build_sw_graph

def sw_pipeline():

	sw_stage_list = []
	cs_stage = ProcessStage(
		name = "CS",
		input_size = [(640, 400, 1)],
        kernel_size = [(16, 16, 1)],
        num_kernels = [64],
        stride = [(16, 16, 1)],
		output_size = (40, 25, 64),
        padding = [False]
	)
	sw_stage_list.append(cs_stage)

	input_data = PixelInput((640, 400, 1), name="Input")
	sw_stage_list.append(input_data)
	cs_stage.set_input_stage(input_data)

	return sw_stage_list

if __name__ == '__main__':

	sw_stage_list = sw_pipeline()
	build_sw_graph(sw_stage_list)







