import path
import sys
import os
  
# directory
parent_directory = os.path.dirname(os.getcwd())
# setting path
sys.path.append(os.path.dirname(parent_directory))

# import local modules
from camj.sw.interface import ProcessStage, DNNProcessStage, PixelInput
from camj.sw.utils import build_sw_graph

def sw_pipeline():

    sw_stage_list = []
    conv_stage = ProcessStage(
        name = "HoG",
        input_size = [(320, 240, 1)],
        kernel_size = [(3, 3, 1)],
        num_kernels = [1],
        stride = [(1, 1, 1)],
        padding = [True]
    )
    sw_stage_list.append(conv_stage)

    input_data = PixelInput((320, 240, 1), name="Input")
    sw_stage_list.append(input_data)
    conv_stage.set_input_stage(input_data)

    return sw_stage_list

if __name__ == '__main__':

    sw_stage_list = sw_pipeline()
    build_sw_graph(sw_stage_list)


