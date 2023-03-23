
import path
import sys
import os
  
# directory reach
parent_directory = os.path.dirname(os.getcwd())
sys.path.append(os.path.dirname(parent_directory))

from camj.sw.interface import ProcessStage, DNNProcessStage, PixelInput
from camj.sw.utils import build_sw_graph

def sw_pipeline():

    sw_stage_list = []

    input_data = PixelInput(name = "Input", size = (1280, 720, 3))
    sw_stage_list.append(input_data)

    comp_stage = ProcessStage(
        name = "MaskComp",
        input_size = [(1280, 720, 3)],
        kernel_size = [(4, 1, 3)],
        num_kernels = [1],
        stride = [(4, 1, 1)],
        padding = [False],
    )
    sw_stage_list.append(comp_stage)

    sampler_stage = ProcessStage(
        name = "Sampler",
        input_size = [(1280, 720, 3)],
        kernel_size = [(2, 1, 1)],
        num_kernels = [1],
        stride = [(2, 1, 1)],
        padding = [False]
    )
    sw_stage_list.append(sampler_stage)

    comp_stage.set_input_stage(input_data)
    sampler_stage.set_input_stage(input_data)

    return sw_stage_list

if __name__ == '__main__':

    sw_stage_list = sw_pipeline()
    build_sw_graph(sw_stage_list)







