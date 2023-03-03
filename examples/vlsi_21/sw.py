
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

    input_data = PixelInput((1668, 1364, 1), name="Input")
    sw_stage_list.append(input_data)

    return sw_stage_list

if __name__ == '__main__':

    sw_stage_list = sw_pipeline()
    build_sw_graph(sw_stage_list)
