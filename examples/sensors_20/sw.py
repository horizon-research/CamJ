import sys
import os
  
# directory reach
parent_directory = os.path.dirname(os.getcwd())
# setting path
sys.path.append(os.path.dirname(parent_directory))

from camj.sim_core.sw_interface import ProcessStage, PixelInput
from camj.sim_core.sw_utils import build_sw_graph

def sw_pipeline():

    sw_stage_list = []

    conv1_stage = ProcessStage(
        name = "Conv-1",
        input_size = [(120, 160, 1)],
        kernel_size = [(2, 2, 1)],
        num_kernels = [1],
        stride = [(2, 2, 1)],
        output_size = (60, 80, 1),
        padding = [False]
    )
    sw_stage_list.append(conv1_stage)

    mp1_stage = ProcessStage(
        name = "MaxPool-1",
        input_size = [(60, 80, 1)],
        kernel_size = [(2, 2, 1)],
        num_kernels = [1],
        stride = [(2, 2, 1)],
        output_size = (30, 40, 1),
        padding = [False]
    )
    sw_stage_list.append(mp1_stage)

    conv2_stage = ProcessStage(
        name = "Conv-2",
        input_size = [(30, 40, 1)],
        kernel_size = [(2, 2, 1)],
        num_kernels = [1],
        stride = [(2, 2, 1)],
        output_size = (15, 20, 1),
        padding = [False]
    )
    sw_stage_list.append(conv2_stage)

    mp2_stage = ProcessStage(
        name = "MaxPool-2",
        input_size = [(16, 20, 1)],
        kernel_size = [(2, 2, 1)],
        num_kernels = [1],
        stride = [(2, 2, 1)],
        output_size = (8, 10, 1),
        padding = [False]
    )
    sw_stage_list.append(mp2_stage)

    fc_stage = ProcessStage(
        name = "FC",
        input_size = [(1, 1, 80)],
        kernel_size = [(1, 1, 80)],
        num_kernels = [1],
        stride = [(1, 1, 1)],
        output_size = (1, 1, 1),
        padding = [False]
    )
    sw_stage_list.append(fc_stage)

    # build the connections among different sw stages
    input_data = PixelInput((128, 128, 1), name="Input")
    sw_stage_list.append(input_data)

    conv1_stage.set_input_stage(input_data)
    mp1_stage.set_input_stage(conv1_stage)
    conv2_stage.set_input_stage(mp1_stage)
    mp2_stage.set_input_stage(conv2_stage)
    fc_stage.set_input_stage(mp2_stage)

    return sw_stage_list

if __name__ == '__main__':

    sw_stage_list = sw_pipeline()
    build_sw_graph(sw_stage_list)





