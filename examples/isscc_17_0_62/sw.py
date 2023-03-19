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

    # NOTE: because this paper use two different image sizes to run digital 
    # and analog simulation, here, we define them separately.
    # this part is the sw definition to run analog simulation
    analog_input_data = PixelInput((240, 320, 1), name = "AnalogInput")
    analog_weight_data = WeightInput((20, 20, 1), name = "Weight")
    sw_stage_list.append(analog_input_data)
    sw_stage_list.append(analog_weight_data)

    binning_stage = ProcessStage(
        name = "Binning",
        input_size = [(240, 320, 1)],
        kernel_size = [(1, 4, 1)],
        num_kernels = [1],
        stride = [(1, 4, 1)],
        padding = [False]
    )
    sw_stage_list.append(binning_stage)

    haar_stage = ProcessStage(
        name = "Haar",
        input_size = [(240, 80, 1)],
        kernel_size = [(20, 20, 1)],
        num_kernels = [1],
        stride = [(1, 11, 1)],
        padding = [False]
    )
    sw_stage_list.append(haar_stage)

    binning_stage.set_input_stage(analog_input_data)
    haar_stage.set_input_stage(binning_stage)    

    scaler = 4
    # this part is the sw definition to run digital simulation
    conv2d_1_stage = DNNProcessStage(
        name = "Conv2D-1",
        op_type = "Conv2D",
        ifmap_size = [128, 128, 1],
        kernel_size = [9, 9, 1, 12*scaler],
        stride = 1
    )
    sw_stage_list.append(conv2d_1_stage)

    mp1_stage = ProcessStage(
        name = "MaxPool-1",
        input_size = [(120, 120, 12*scaler)],
        kernel_size = [(2, 2, 1)],
        num_kernels = [1],
        stride = [(2, 2, 1)],
        padding = [False]
    )
    sw_stage_list.append(mp1_stage)

    conv2d_2_1_stage = DNNProcessStage(
        name = "Conv2D-2-1",
        op_type = "Conv2D",
        ifmap_size = [60, 60, 12*scaler],
        kernel_size = [5, 1, 12*scaler, 12*scaler],
        stride = 1
    )
    sw_stage_list.append(conv2d_2_1_stage)

    conv2d_2_2_stage = DNNProcessStage(
        name = "Conv2D-2-2",
        op_type = "Conv2D",
        ifmap_size = [56, 60, 12*scaler],
        kernel_size = [1, 5, 12*scaler, 24*scaler],
        stride = 1
    )
    sw_stage_list.append(conv2d_2_2_stage)

    mp2_stage = ProcessStage(
        name = "MaxPool-2",
        input_size = [(56, 56, 24*scaler)],
        kernel_size = [(2, 2, 1)],
        num_kernels = [1],
        stride = [(2, 2, 1)],
        padding = [False]
    )
    sw_stage_list.append(mp2_stage)

    conv2d_3_stage = DNNProcessStage(
        name = "Conv2D-3",
        op_type = "Conv2D",
        ifmap_size = [28, 28, 24*scaler],
        kernel_size = [5, 5, 24*scaler, 36*scaler],
        stride = 1
    )
    sw_stage_list.append(conv2d_3_stage)

    mp3_stage = ProcessStage(
        name = "MaxPool-3",
        input_size = [(24, 24, 36*scaler)],
        kernel_size = [(2, 2, 1)],
        num_kernels = [1],
        stride = [(2, 2, 1)],
        padding = [False]
    )
    sw_stage_list.append(mp3_stage)

    conv2d_4_stage = DNNProcessStage(
        name = "Conv2D-4",
        op_type = "Conv2D",
        ifmap_size = [12, 12, 36*scaler],
        kernel_size = [3, 3, 36*scaler, 48*scaler],
        stride = 1
    )
    sw_stage_list.append(conv2d_4_stage)

    mp4_stage = ProcessStage(
        name = "MaxPool-4",
        input_size = [(10, 10, 48*scaler)],
        kernel_size = [(2, 2, 1)],
        num_kernels = [1],
        stride = [(2, 2, 1)],
        padding = [False]
    )
    sw_stage_list.append(mp4_stage)

    fc_1_stage = DNNProcessStage(
        name = "FC-1",
        op_type = "FC",
        ifmap_size = [1, 1, 1200*scaler],
        kernel_size = [1, 1, 1200*scaler, 256],
        stride = 1
    )
    sw_stage_list.append(fc_1_stage)

    input_data = PixelInput((128, 128, 1), name="Input")
    sw_stage_list.append(input_data)

    conv2d_1_stage.set_input_stage(input_data)
    mp1_stage.set_input_stage(conv2d_1_stage)

    conv2d_2_1_stage.set_input_stage(mp1_stage)
    conv2d_2_2_stage.set_input_stage(conv2d_2_1_stage)
    mp2_stage.set_input_stage(conv2d_2_2_stage)

    conv2d_3_stage.set_input_stage(mp2_stage)
    mp3_stage.set_input_stage(conv2d_3_stage)

    conv2d_4_stage.set_input_stage(mp3_stage)
    mp4_stage.set_input_stage(conv2d_4_stage)

    fc_1_stage.set_input_stage(mp4_stage)

    return sw_stage_list

if __name__ == '__main__':

    sw_stage_list = sw_pipeline()
    build_sw_graph(sw_stage_list)







