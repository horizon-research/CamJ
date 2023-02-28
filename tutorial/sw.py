import sys
import os

# setting path
sys.path.append(os.path.dirname(os.getcwd()))

from camj.sim_core.sw_interface import ProcessStage, PixelInput
from camj.sim_core.sw_utils import build_sw_graph

def sw_pipeline():

    sw_stage_list = []
    # define input data
    input_data = PixelInput((32, 32, 1), name="Input")
    
    # define a 3x3 convolution stage
    conv_stage = ProcessStage(
        name = "Conv",
        input_size = [(32, 32, 1)],
        kernel_size = [(3, 3, 1)],
        num_kernels = [1],
        stride = [(1, 1, 1)],
        output_size = (32, 32, 1),
        padding = [True]
    )
    
    # define a 1x1 absolution stage
    abs_stage = ProcessStage(
        name = "Abs",
        input_size = [(32, 32, 1)],
        kernel_size = [(1, 1, 1)],
        num_kernels = [1],
        stride = [(1, 1, 1)],
        output_size = (32, 32, 1),
        padding = [False]
    )

    # set data dependency
    conv_stage.set_input_stage(input_data)
    abs_stage.set_input_stage(conv_stage)

    sw_stage_list.append(input_data)
    sw_stage_list.append(conv_stage)
    sw_stage_list.append(abs_stage)

    return sw_stage_list

if __name__ == '__main__':

    sw_stage_list = sw_pipeline()
    build_sw_graph(sw_stage_list)



