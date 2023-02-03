import path
import sys
import os

# directory reach
directory = os.getcwd()
parent_directory = os.path.dirname(directory)
# setting path
sys.path.append(os.path.dirname(directory))
sys.path.append(os.path.dirname(parent_directory))

from sw_framework_interface import ProcessStage, DNNProcessStage, PixelInput, build_sw_graph


def sw_pipeline():
    sw_stage_list = []
    conv_stage = ProcessStage(
        name="Conv",
        input_size=[(126, 126, 1)],
        output_size=(42, 42, 8),
        input_reuse=[(1, 1, 1)]
    )
    sw_stage_list.append(conv_stage)

    mp_stage = ProcessStage(
        name="MaxPool",
        input_size=[(42, 42, 8)],
        output_size=(21, 21, 8),
        input_reuse=[(1, 1, 1)]
    )
    sw_stage_list.append(mp_stage)

    input_data = PixelInput((126, 126, 1), name="Input")
    sw_stage_list.append(input_data)

    conv_stage.set_input_stage(input_data)

    mp_stage.set_input_stage(conv_stage)

    return sw_stage_list


if __name__ == '__main__':
    sw_stage_list = sw_pipeline()
    build_sw_graph(sw_stage_list)
