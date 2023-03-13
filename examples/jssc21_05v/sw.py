
import path
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
    conv_stage = ProcessStage(
        name = "Conv",
        input_size = [(128, 128, 1)],
        kernel_size = [(3, 3, 1)],
        num_kernels = [1],
        stride = [(1, 1, 1)],
        padding = [False]
    )
    sw_stage_list.append(conv_stage)

    input_data = PixelInput((128, 128, 1), name="Input")
    weight_data = PixelInput((3, 3, 1), name="Weight")
    sw_stage_list.append(input_data)
    sw_stage_list.append(weight_data)
    conv_stage.set_input_stage(input_data)
    conv_stage.set_input_stage(weight_data)

    return sw_stage_list

if __name__ == '__main__':

    sw_stage_list = sw_pipeline()
    build_sw_graph(sw_stage_list)







