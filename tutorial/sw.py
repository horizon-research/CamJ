import sys
import os

# setting path
sys.path.append(os.path.dirname(os.getcwd()))

from camj.sim_core.sw_interface import ProcessStage, PixelInput
from camj.sim_core.sw_utils import build_sw_graph

def sw_pipeline():

    sw_stage_list = []
    # define input data
    input_data = PixelInput((36, 36, 1), name="Input")
    
    # define a 3x3 convolution stage with stride of 1
    conv1_stage = ProcessStage(
        name = "Conv1",
        input_size = [(36, 36, 1)], # (H, W, C)
        kernel_size = [(3, 3, 1)],  # (K_h, K_w, K_c)
        num_kernels = [1],
        stride = [(1, 1, 1)],       # (H, W, C)
        output_size = (36, 36, 1),  # with padding and stride of 1
        padding = [True]            # output size is the same as input
    )

    # define a 3x3 convolution stage with stride of 3
    conv2_stage = ProcessStage(
        name = "Conv2",
        input_size = [(36, 36, 1)], # (H, W, C)
        kernel_size = [(3, 3, 1)],  # (K_h, K_w, K_c) 
        num_kernels = [1],
        stride = [(3, 3, 1)],       # (H, W, C)
        output_size = (12, 12, 1),  # with no padding and stride of 3
        padding = [False]           # output size becomes (12, 12, 1)
    )
    
    # define a 1x1 absolution stage
    abs_stage = ProcessStage(
        name = "Abs",
        input_size = [(12, 12, 1)], # (H, W, C)
        kernel_size = [(1, 1, 1)],  # (K_h, K_w, K_c) 
        num_kernels = [1],
        stride = [(1, 1, 1)],       # (H, W, C)
        output_size = (12, 12, 1),  # same as input size
        padding = [False]
    )

    # set data dependency
    conv1_stage.set_input_stage(input_data)
    conv2_stage.set_input_stage(conv1_stage)
    abs_stage.set_input_stage(conv2_stage)

    sw_stage_list.append(input_data)
    sw_stage_list.append(conv1_stage)
    sw_stage_list.append(conv2_stage)
    sw_stage_list.append(abs_stage)

    return sw_stage_list

if __name__ == '__main__':

    sw_stage_list = sw_pipeline()
    build_sw_graph(sw_stage_list)



