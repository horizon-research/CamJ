
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
    fc1_stage = ProcessStage(
        name = "FC1",
        input_size = [(32, 32, 1)],
        kernel_size = [(32, 32, 1)],
        num_kernels = [16],
        stride = [(1, 1, 1)],
        output_size = (1, 1, 16),
        padding = [False]
    )
    sw_stage_list.append(fc1_stage)

    fc2_stage = ProcessStage(
        name = "FC2",
        input_size = [(1, 1, 16)],
        kernel_size = [(1, 1, 16)],
        num_kernels = [10],
        stride = [(1, 1, 1)],
        output_size = (1, 1, 10),
        padding = [False]
    )
    sw_stage_list.append(fc2_stage)

    # build the connections among different sw stages
    input_data = PixelInput((32, 32, 1), name="Input")
    sw_stage_list.append(input_data)

    fc1_stage.set_input_stage(input_data)
    fc2_stage.set_input_stage(fc1_stage)

    return sw_stage_list

if __name__ == '__main__':

    sw_stage_list = sw_pipeline()
    build_sw_graph(sw_stage_list)





