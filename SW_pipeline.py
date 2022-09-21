import path
import sys
import os

# directory reach
directory = os.getcwd()

# setting path
sys.path.append(os.path.dirname(directory))

from framework.sw_framework_interface import ProcessStage, DNNProcessStage, PixelInput, build_sw_graph


def sw_pipeline_case2(K=8):
    sw_stage_list = []
    ImageCapture_stage = PixelInput(
        name="ImageCapture",
        input_size=[126, 126, 1],  # light
        output_size=[126, 126, 1]
    )
    sw_stage_list.append(ImageCapture_stage)

    conv2d_stage = DNNProcessStage(
        name="Conv2D",
        op_type="Conv2D",
        ifmap_size=[126, 126, 1],
        kernel_size=[3, 3, 1, K],  # [height,width,input_channel,output_channel]
        stride=3
    )
    sw_stage_list.append(conv2d_stage)

    relu_stage = DNNProcessStage(
        name="ReLU",
        op_type="ReLU",
        ifmap_size=[42, 42, K]
    )
    sw_stage_list.append(relu_stage)

    maxpooling_stage = DNNProcessStage(
        name="MaxPooling",
        op_type="MaxPooling",
        ifmap_size=[42, 42, K],
        kernel_size=[2, 2, 1, 1],
        stride=2
    )
    sw_stage_list.append(maxpooling_stage)

    quantization_stage = ProcessStage(
        name="Quantization",
        input_size=[21, 21, K],
        output_size=[21, 21, K]
    )
    sw_stage_list.append(quantization_stage)

    fc_stage = DNNProcessStage(
        name="FC",
        op_type="FC",
        ifmap_size=[21, 21, K],
        kernel_size=[21, 21, K],
        stride=1
    )
    sw_stage_list.append(fc_stage)

    conv2d_stage.set_input_stage(ImageCapture_stage)
    relu_stage.set_input_stage(conv2d_stage)
    maxpooling_stage.set_input_stage(relu_stage)
    quantization_stage.set_input_stage(maxpooling_stage)
    fc_stage.set_input_stage(quantization_stage)

    return sw_stage_list


def sw_pipeline_case3():
    sw_stage_list = []
    ImageCapture_stage = PixelInput(
        name="ImageCapture",
        input_size=(1, 160, 1),  # light
        output_size=(1, 160, 1)
    )
    sw_stage_list.append(ImageCapture_stage)

    CDS_stage = ProcessStage(
        name="Thresholding",
        input_size=(1, 160, 1),
        output_size=(1, 160, 1)
    )
    sw_stage_list.append(CDS_stage)

    conv2d_1_stage = DNNProcessStage(
        name="Conv2D_1",
        op_type="Conv2D",
        ifmap_size=[120, 160, 1],
        kernel_size=[2, 2, 1, 1],
        stride=2
    )
    sw_stage_list.append(conv2d_1_stage)

    maxpooling_1_stage = DNNProcessStage(
        name="MaxPooling_1",
        op_type="MaxPooling",
        ifmap_size=[60, 80, 1],
        kernel_size=[2, 2, 1, 1],
        stride=2
    )
    sw_stage_list.append(maxpooling_1_stage)

    conv2d_2_stage = DNNProcessStage(
        name="Conv2D_2",
        op_type="Conv2D",
        ifmap_size=[30, 40, 1],
        kernel_size=[2, 2, 1, 1],
        stride=2
    )
    sw_stage_list.append(conv2d_2_stage)

    maxpooling_2_stage = DNNProcessStage(
        name="MaxPooling_2",
        op_type="MaxPooling",
        ifmap_size=[15, 20, 1],
        kernel_size=[2, 2, 1, 1],
        stride=2
    )
    sw_stage_list.append(maxpooling_2_stage)

    quantization_stage = ProcessStage(
        name="Quantization",
        input_size=(8, 10, 1),
        output_size=(8, 10, 1)
    )
    sw_stage_list.append(quantization_stage)

    fc_stage = DNNProcessStage(
        name="FC",
        op_type="FC",
        ifmap_size=[80, 1, 1],
        kernel_size=[80, 1],
        stride=1
    )
    sw_stage_list.append(fc_stage)

    CDS_stage.set_input_stage(ImageCapture_stage)
    conv2d_1_stage.set_input_stage(CDS_stage)
    maxpooling_1_stage.set_input_stage(conv2d_1_stage)
    conv2d_2_stage.set_input_stage(maxpooling_1_stage)
    maxpooling_2_stage.set_input_stage(conv2d_2_stage)
    quantization_stage.set_input_stage(maxpooling_2_stage)
    fc_stage.set_input_stage(quantization_stage)

    return sw_stage_list


if __name__ == '__main__':
    sw_stage_list = sw_pipeline_case3()
    build_sw_graph(sw_stage_list)
