import sys
import os

# directory reach
parent_directory = os.path.dirname(os.getcwd())
sys.path.append(os.path.dirname(parent_directory))

from camj.sw.interface import ProcessStage, DNNProcessStage, PixelInput, WeightInput
from camj.sw.utils import build_sw_graph

def sw_pipeline():

    sw_stage_list = []
    input_data = PixelInput(
        name = "CurrInput",
        size = (640, 400, 1),
    )
    sw_stage_list.append(input_data)

    prev_input_data = PixelInput(
        name = "PrevInput",
        size = (640, 400, 1),
    )
    sw_stage_list.append(prev_input_data)

    curr_resize_stage = ProcessStage(
        name = "CurrResize",
        input_size = [(400, 640, 1)],
        kernel_size = [(2, 2, 1)],
        num_kernels = [1],
        stride = [(2, 2, 1)],
        padding =[False]
    )
    sw_stage_list.append(curr_resize_stage)

    prev_resize_stage = ProcessStage(
        name = "PrevResize",
        input_size = [(400, 640, 1)],
        kernel_size = [(2, 2, 1)],
        num_kernels = [1],
        stride = [(2, 2, 1)],
        padding = [False]
    )
    sw_stage_list.append(prev_resize_stage)

    eventification_stage = ProcessStage(
        name = "Eventification",
        input_size = [(200, 320, 1), (200, 320, 1)],
        kernel_size = [(1, 1, 1), (1, 1, 1)],
        num_kernels = [1, 1],
        stride = [(1, 1, 1), (1, 1, 1)],
        padding = [False, False]
    )
    sw_stage_list.append(eventification_stage)

    thresholding_stage = ProcessStage(
        name = "Thresholding",
        input_size = [(1, 4, 1), (200, 320, 1)],
        kernel_size = [(1, 4, 1), (200, 320, 1)],
        num_kernels = [1, 1],
        stride = [(1, 4, 1), (200, 320, 1)],
        padding = [False, False]
    )
    sw_stage_list.append(thresholding_stage)

    conv2d_1_stage = DNNProcessStage(
        name = "Conv2D_1",
        op_type = "Conv2D",
        ifmap_size = [200, 320, 1],
        kernel_size = [3, 3, 1, 32],
        stride = 2
    )
    sw_stage_list.append(conv2d_1_stage)

    conv2d_2_stage = DNNProcessStage(
        name = "Conv2D_2",
        op_type = "Conv2D",
        ifmap_size = [100, 160, 32],
        kernel_size = [3, 3, 32, 32],
        stride = 2
    )
    sw_stage_list.append(conv2d_2_stage)

    conv2d_3_stage = DNNProcessStage(
        name = "Conv2D_3",
        op_type = "Conv2D",
        ifmap_size = [50, 80, 32],
        kernel_size = [3, 3, 32, 32],
        stride = 2
    )
    sw_stage_list.append(conv2d_3_stage)

    fc_1_stage = DNNProcessStage(
        name = "FC_1",
        op_type = "FC",
        ifmap_size = [1, 1, 1000],
        kernel_size = [1, 1, 1000, 32],
        stride = 1
    )
    sw_stage_list.append(fc_1_stage)

    fc_2_stage = DNNProcessStage(
        name = "FC_2",
        op_type = "FC",
        ifmap_size = [1, 1, 32],
        kernel_size = [1, 1, 32, 4],
        stride = 1
    )
    sw_stage_list.append(fc_2_stage)

    curr_resize_stage.set_input_stage(input_data)
    prev_resize_stage.set_input_stage(prev_input_data)

    eventification_stage.set_input_stage(curr_resize_stage)
    eventification_stage.set_input_stage(prev_resize_stage)

    conv2d_1_stage.set_input_stage(eventification_stage)

    conv2d_2_stage.set_input_stage(conv2d_1_stage)

    conv2d_3_stage.set_input_stage(conv2d_2_stage)

    conv2d_3_stage.flatten()

    fc_1_stage.set_input_stage(conv2d_3_stage)
    fc_2_stage.set_input_stage(fc_1_stage)  

    thresholding_stage.set_input_stage(fc_2_stage)
    thresholding_stage.set_input_stage(eventification_stage)

    return sw_stage_list


def sw_pipeline_w_analog():

    sw_stage_list = []
    input_data = PixelInput(
        name = "CurrInput",
        size = (640, 400, 1),
    )
    sw_stage_list.append(input_data)

    prev_resized_input_data = WeightInput(
        name = "PrevResizedInput",
        size = (320, 200, 1), 
        
    )
    sw_stage_list.append(prev_resized_input_data)

    curr_resize_stage = ProcessStage(
        name = "CurrResize",
        input_size = [(400, 640, 1)],
        kernel_size = [(2, 2, 1)],
        num_kernels = [1],
        stride = [(2, 2, 1)],
        padding =[False]
    )
    sw_stage_list.append(curr_resize_stage)

    eventification_stage = ProcessStage(
        name = "Eventification",
        input_size = [(200, 320, 1), (200, 320, 1)],
        kernel_size = [(1, 1, 1), (1, 1, 1)],
        num_kernels = [1, 1],
        stride = [(1, 1, 1), (1, 1, 1)],
        padding = [False, False],
    )
    sw_stage_list.append(eventification_stage)

    thresholding_stage = ProcessStage(
        name = "Thresholding",
        input_size = [(1, 4, 1), (200, 320, 1)],
        kernel_size = [(1, 4, 1), (200, 320, 1)],
        num_kernels = [1, 1],
        stride = [(1, 4, 1), (200, 320, 1)],
        padding = [False, False]
    )
    sw_stage_list.append(thresholding_stage)

    conv2d_1_stage = DNNProcessStage(
        name = "Conv2D_1",
        op_type = "Conv2D",
        ifmap_size = [200, 320, 1],
        kernel_size = [3, 3, 1, 32],
        stride = 2
    )
    sw_stage_list.append(conv2d_1_stage)

    conv2d_2_stage = DNNProcessStage(
        name = "Conv2D_2",
        op_type = "Conv2D",
        ifmap_size = [100, 160, 32],
        kernel_size = [3, 3, 32, 32],
        stride = 2
    )
    sw_stage_list.append(conv2d_2_stage)

    conv2d_3_stage = DNNProcessStage(
        name = "Conv2D_3",
        op_type = "Conv2D",
        ifmap_size = [50, 80, 32],
        kernel_size = [3, 3, 32, 32],
        stride = 2
    )
    sw_stage_list.append(conv2d_3_stage)

    fc_1_stage = DNNProcessStage(
        name = "FC_1",
        op_type = "FC",
        ifmap_size = [1, 1, 1000],
        kernel_size = [1, 1, 1000, 32],
        stride = 1
    )
    sw_stage_list.append(fc_1_stage)

    fc_2_stage = DNNProcessStage(
        name = "FC_2",
        op_type = "FC",
        ifmap_size = [1, 1, 32],
        kernel_size = [1, 1, 32, 4],
        stride = 1
    )
    sw_stage_list.append(fc_2_stage)

    curr_resize_stage.set_input_stage(input_data)

    eventification_stage.set_input_stage(curr_resize_stage)
    eventification_stage.set_input_stage(prev_resized_input_data)

    conv2d_1_stage.set_input_stage(eventification_stage)

    conv2d_2_stage.set_input_stage(conv2d_1_stage)

    conv2d_3_stage.set_input_stage(conv2d_2_stage)

    conv2d_3_stage.flatten()

    fc_1_stage.set_input_stage(conv2d_3_stage)
    fc_2_stage.set_input_stage(fc_1_stage)  

    thresholding_stage.set_input_stage(fc_2_stage)
    thresholding_stage.set_input_stage(eventification_stage)

    return sw_stage_list

if __name__ == '__main__':
    # test the sw pipeline without analog computing
    # sw_stage_list = sw_pipeline()
    # build_sw_graph(sw_stage_list)
    # test the sw pipeline with analog computing
    sw_stage_list = sw_pipeline_w_analog()
    build_sw_graph(sw_stage_list)







