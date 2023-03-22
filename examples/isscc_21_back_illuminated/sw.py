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

    input_data = PixelInput(name = "Input", size = (3040, 4056, 1))
    sw_stage_list.append(input_data)

    resized_input_data = PixelInput(name = "ResizedInput", size = (224, 224, 3))
    sw_stage_list.append(resized_input_data)

    conv2d_1_stage = DNNProcessStage(
        name = "Conv2D-1",
        op_type = "Conv2D",
        ifmap_size = [224, 224, 3],
        kernel_size = [3, 3, 3, 32],
        stride = 2
    )
    sw_stage_list.append(conv2d_1_stage)

    dwconv2d_1_stage = DNNProcessStage(
        name = "DWConv2D-1",
        op_type = "DWConv2D",
        ifmap_size = [112, 112, 32],
        kernel_size = [3, 3, 32, 32],
        stride = 1
    )
    sw_stage_list.append(dwconv2d_1_stage)

    conv2d_2_stage = DNNProcessStage(
        name = "Conv2D-2",
        op_type = "Conv2D",
        ifmap_size = [112, 112, 32],
        kernel_size = [1, 1, 32, 64],
        stride = 1
    )
    sw_stage_list.append(conv2d_2_stage)

    dwconv2d_2_stage = DNNProcessStage(
        name = "DWConv2D-2",
        op_type = "DWConv2D",
        ifmap_size = [112, 112, 64],
        kernel_size = [3, 3, 64, 64],
        stride = 2
    )
    sw_stage_list.append(dwconv2d_2_stage)

    conv2d_3_stage = DNNProcessStage(
        name = "Conv2D-3",
        op_type = "Conv2D",
        ifmap_size = [56, 56, 64],
        kernel_size = [1, 1, 64, 128],
        stride = 1
    )
    sw_stage_list.append(conv2d_3_stage)

    dwconv2d_3_stage = DNNProcessStage(
        name = "DWConv2D-3",
        op_type = "DWConv2D",
        ifmap_size = [56, 56, 128],
        kernel_size = [3, 3, 128, 128],
        stride = 1
    )
    sw_stage_list.append(dwconv2d_3_stage)

    conv2d_4_stage = DNNProcessStage(
        name = "Conv2D-4",
        op_type = "Conv2D",
        ifmap_size = [56, 56, 128],
        kernel_size = [1, 1, 128, 128],
        stride = 1
    )
    sw_stage_list.append(conv2d_4_stage)

    dwconv2d_4_stage = DNNProcessStage(
        name = "DWConv2D-4",
        op_type = "DWConv2D",
        ifmap_size = [56, 56, 128],
        kernel_size = [3, 3, 128, 128],
        stride = 2
    )
    sw_stage_list.append(dwconv2d_4_stage)

    conv2d_5_stage = DNNProcessStage(
        name = "Conv2D-5",
        op_type = "Conv2D",
        ifmap_size = [28, 28, 128],
        kernel_size = [1, 1, 128, 256],
        stride = 1
    )
    sw_stage_list.append(conv2d_5_stage)

    dwconv2d_5_stage = DNNProcessStage(
        name = "DWConv2D-5",
        op_type = "DWConv2D",
        ifmap_size = [28, 28, 256],
        kernel_size = [3, 3, 256, 256],
        stride = 1
    )
    sw_stage_list.append(dwconv2d_5_stage)

    conv2d_6_stage = DNNProcessStage(
        name = "Conv2D-6",
        op_type = "Conv2D",
        ifmap_size = [28, 28, 256],
        kernel_size = [1, 1, 256, 256],
        stride = 1
    )
    sw_stage_list.append(conv2d_6_stage)

    dwconv2d_6_stage = DNNProcessStage(
        name = "DWConv2D-6",
        op_type = "DWConv2D",
        ifmap_size = [28, 28, 256],
        kernel_size = [3, 3, 256, 256],
        stride = 2
    )
    sw_stage_list.append(dwconv2d_6_stage)

    conv2d_7_stage = DNNProcessStage(
        name = "Conv2D-7",
        op_type = "Conv2D",
        ifmap_size = [14, 14, 256],
        kernel_size = [1, 1, 256, 512],
        stride = 1
    )
    sw_stage_list.append(conv2d_7_stage)

    dwconv2d_1_1_stage = DNNProcessStage(
        name = "DWConv2D-1-1",
        op_type = "DWConv2D",
        ifmap_size = [14, 14, 512],
        kernel_size = [3, 3, 512, 512],
        stride = 1
    )
    sw_stage_list.append(dwconv2d_1_1_stage)

    conv2d_1_1_stage = DNNProcessStage(
        name = "Conv2D-1-1",
        op_type = "Conv2D",
        ifmap_size = [14, 14, 512],
        kernel_size = [1, 1, 512, 512],
        stride = 1
    )
    sw_stage_list.append(conv2d_1_1_stage)

    dwconv2d_1_2_stage = DNNProcessStage(
        name = "DWConv2D-1-2",
        op_type = "DWConv2D",
        ifmap_size = [14, 14, 512],
        kernel_size = [3, 3, 512, 512],
        stride = 1
    )
    sw_stage_list.append(dwconv2d_1_2_stage)

    conv2d_1_2_stage = DNNProcessStage(
        name = "Conv2D-1-2",
        op_type = "Conv2D",
        ifmap_size = [14, 14, 512],
        kernel_size = [1, 1, 512, 512],
        stride = 1
    )
    sw_stage_list.append(conv2d_1_2_stage)

    dwconv2d_1_3_stage = DNNProcessStage(
        name = "DWConv2D-1-3",
        op_type = "DWConv2D",
        ifmap_size = [14, 14, 512],
        kernel_size = [3, 3, 512, 512],
        stride = 1
    )
    sw_stage_list.append(dwconv2d_1_3_stage)

    conv2d_1_3_stage = DNNProcessStage(
        name = "Conv2D-1-3",
        op_type = "Conv2D",
        ifmap_size = [14, 14, 512],
        kernel_size = [1, 1, 512, 512],
        stride = 1
    )
    sw_stage_list.append(conv2d_1_3_stage)

    dwconv2d_1_4_stage = DNNProcessStage(
        name = "DWConv2D-1-4",
        op_type = "DWConv2D",
        ifmap_size = [14, 14, 512],
        kernel_size = [3, 3, 512, 512],
        stride = 1
    )
    sw_stage_list.append(dwconv2d_1_4_stage)

    conv2d_1_4_stage = DNNProcessStage(
        name = "Conv2D-1-4",
        op_type = "Conv2D",
        ifmap_size = [14, 14, 512],
        kernel_size = [1, 1, 512, 512],
        stride = 1
    )
    sw_stage_list.append(conv2d_1_4_stage)

    dwconv2d_1_5_stage = DNNProcessStage(
        name = "DWConv2D-1-5",
        op_type = "DWConv2D",
        ifmap_size = [14, 14, 512],
        kernel_size = [3, 3, 512, 512],
        stride = 1
    )
    sw_stage_list.append(dwconv2d_1_5_stage)

    conv2d_1_5_stage = DNNProcessStage(
        name = "Conv2D-1-5",
        op_type = "Conv2D",
        ifmap_size = [14, 14, 512],
        kernel_size = [1, 1, 512, 512],
        stride = 1
    )
    sw_stage_list.append(conv2d_1_5_stage)

    dwconv2d_7_stage = DNNProcessStage(
        name = "DWConv2D-7",
        op_type = "DWConv2D",
        ifmap_size = [14, 14, 512],
        kernel_size = [3, 3, 512, 1024],
        stride = 2
    )
    sw_stage_list.append(dwconv2d_7_stage)

    conv2d_8_stage = DNNProcessStage(
        name = "Conv2D-8",
        op_type = "Conv2D",
        ifmap_size = [7, 7, 1024],
        kernel_size = [1, 1, 1024, 1024],
        stride = 1
    )
    sw_stage_list.append(conv2d_8_stage)

    dwconv2d_8_stage = DNNProcessStage(
        name = "DWConv2D-8",
        op_type = "DWConv2D",
        ifmap_size = [7, 7, 1024],
        kernel_size = [3, 3, 1024, 1024],
        stride = 1
    )
    sw_stage_list.append(dwconv2d_8_stage)

    conv2d_9_stage = DNNProcessStage(
        name = "Conv2D-9",
        op_type = "Conv2D",
        ifmap_size = [7, 7, 1024],
        kernel_size = [1, 1, 1024, 1024],
        stride = 1
    )
    sw_stage_list.append(conv2d_9_stage)

    mp_stage = ProcessStage(
        name = "AvgPool",
        input_size = [(7, 7, 1024)],
        kernel_size = [(7, 7, 1)],
        num_kernels = [1],
        stride = [(7, 7, 1)],
        padding = [False]
    )
    sw_stage_list.append(mp_stage)
    
    fc_1_stage = DNNProcessStage(
        name = "FC-1",
        op_type = "FC",
        ifmap_size = [1, 1, 1024,],
        kernel_size = [1, 1, 1024, 1000],
        stride = 1
    )
    sw_stage_list.append(fc_1_stage)

    conv2d_1_stage.set_input_stage(resized_input_data)
    dwconv2d_1_stage.set_input_stage(conv2d_1_stage)

    conv2d_2_stage.set_input_stage(dwconv2d_1_stage)
    dwconv2d_2_stage.set_input_stage(conv2d_2_stage)

    conv2d_3_stage.set_input_stage(dwconv2d_2_stage)
    dwconv2d_3_stage.set_input_stage(conv2d_3_stage)

    conv2d_4_stage.set_input_stage(dwconv2d_3_stage)
    dwconv2d_4_stage.set_input_stage(conv2d_4_stage)

    conv2d_5_stage.set_input_stage(dwconv2d_4_stage)
    dwconv2d_5_stage.set_input_stage(conv2d_5_stage)

    conv2d_6_stage.set_input_stage(dwconv2d_5_stage)
    dwconv2d_6_stage.set_input_stage(conv2d_6_stage)

    conv2d_7_stage.set_input_stage(dwconv2d_6_stage)

    dwconv2d_1_1_stage.set_input_stage(conv2d_7_stage)
    conv2d_1_1_stage.set_input_stage(dwconv2d_1_1_stage)

    dwconv2d_1_2_stage.set_input_stage(conv2d_1_1_stage)
    conv2d_1_2_stage.set_input_stage(dwconv2d_1_2_stage)

    dwconv2d_1_3_stage.set_input_stage(conv2d_1_2_stage)
    conv2d_1_3_stage.set_input_stage(dwconv2d_1_3_stage)

    dwconv2d_1_4_stage.set_input_stage(conv2d_1_3_stage)
    conv2d_1_4_stage.set_input_stage(dwconv2d_1_4_stage)

    dwconv2d_1_5_stage.set_input_stage(conv2d_1_4_stage)
    conv2d_1_5_stage.set_input_stage(dwconv2d_1_5_stage)

    dwconv2d_7_stage.set_input_stage(conv2d_1_5_stage)

    conv2d_8_stage.set_input_stage(dwconv2d_7_stage)
    dwconv2d_8_stage.set_input_stage(conv2d_8_stage)

    conv2d_9_stage.set_input_stage(dwconv2d_8_stage)

    mp_stage.set_input_stage(conv2d_9_stage)

    fc_1_stage.set_input_stage(mp_stage)

    return sw_stage_list

if __name__ == '__main__':

    sw_stage_list = sw_pipeline()
    build_sw_graph(sw_stage_list)







