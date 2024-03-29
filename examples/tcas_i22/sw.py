import sys
import os
  
# directory reach
parent_directory = os.path.dirname(os.getcwd())
# setting path
sys.path.append(os.path.dirname(parent_directory))

from camj.sw.interface import ProcessStage, DNNProcessStage, PixelInput
from camj.sw.utils import build_sw_graph

def sw_pipeline():

    sw_stage_list = []

    # build the connections among different sw stages
    input_data = PixelInput(
        name = "Input", 
        size = (1, 1, 1), # here it defines output size, in this case is 1x1. 
        
    )
    sw_stage_list.append(input_data)

    return sw_stage_list

if __name__ == '__main__':

    sw_stage_list = sw_pipeline()
    build_sw_graph(sw_stage_list)

