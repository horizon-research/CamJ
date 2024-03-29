import sys
import os
  
# directory reach
parent_directory = os.path.dirname(os.getcwd())
# setting path
sys.path.append(os.path.dirname(parent_directory))

from camj.sw.interface import ProcessStage, DNNProcessStage, PixelInput, WeightInput
from camj.sw.utils import build_sw_graph

def sw_pipeline():

    sw_stage_list = []

    input_data = PixelInput(name = "Input", size = (126, 126, 1))
    sw_stage_list.append(input_data)

    weight_data = WeightInput(name = "Weight", size = (3, 3, 8))
    sw_stage_list.append(weight_data)

    conv_stage = ProcessStage(
        name = "Conv",
        input_size = [(126, 126, 1)],
        kernel_size = [(3, 3, 1)],
        num_kernels = [8],
        stride = [(3, 3, 1)],
        padding = [False]
    )
    sw_stage_list.append(conv_stage)

    relu_stage = ProcessStage(
        name = "ReLU",
        input_size = [(42, 42, 8)],
        kernel_size = [(1, 1, 1)],
        num_kernels = [1],
        stride = [(1, 1, 1)],
        padding = [False]
    )
    sw_stage_list.append(relu_stage)

    mp_stage = ProcessStage(
        name = "MaxPool",
        input_size = [(42, 42, 8)],
        kernel_size = [(2, 2, 1)],
        num_kernels = [1],
        stride = [(2, 2, 1)],
        padding = [False]
    )
    sw_stage_list.append(mp_stage)

    fc_stage = ProcessStage(
        name = "FC",
        input_size = [(21, 21, 8)],
        kernel_size = [(21, 21, 8)],
        num_kernels = [1],
        stride = [(1, 1, 1)],
        padding = [False]
    )
    sw_stage_list.append(fc_stage)

    # build the connections among different sw stages
    conv_stage.set_input_stage(input_data)
    conv_stage.set_input_stage(weight_data)

    relu_stage.set_input_stage(conv_stage)
    
    mp_stage.set_input_stage(relu_stage)

    fc_stage.set_input_stage(mp_stage)

    return sw_stage_list

if __name__ == '__main__':

    sw_stage_list = sw_pipeline()
    build_sw_graph(sw_stage_list)





