
import path
import sys
import os
  
# directory reach
directory = os.getcwd()
  
# setting path
sys.path.append(os.path.dirname(directory))

from sw_framework_interface import ProcessStage, DNNProcessStage, PixelInput, build_sw_graph

def sw_pipeline():

	sw_stage_list = []
	eventification_stage = ProcessStage(
		name = "Eventification",
		input_size = [(64, 64, 1), (64, 64, 1)],
		output_size = (64, 64, 1),
		input_reuse = [(1, 1, 1), (1, 1, 1)]
	)
	sw_stage_list.append(eventification_stage)

	thresholding_stage = ProcessStage(
		name = "Thresholding",
		input_size = [(4, 1, 1), (256, 256, 1)],
		output_size = (1, 1, 1),
		input_reuse = [(1, 1, 1), (1, 1, 1)]
	)
	sw_stage_list.append(thresholding_stage)

	# edge_dectection_stage = ProcessStage(
	# 	name = "EdgeDetection",
	# 	input_size = [(256, 256, 1)],
	# 	output_size = (256, 256, 1)
	# )
	# sw_stage_list.append(edge_dectection_stage)

	# bbox_find_stage = ProcessStage(
	# 	name = "BBoxFinding",
	# 	input_size = [(256, 256, 1)],
	# 	output_size = (4, 1, 1)
	# )
	# sw_stage_list.append(bbox_find_stage)

	conv2d_1_stage = DNNProcessStage(
		name = "Conv2D_1",
		op_type = "Conv2D",
		ifmap_size = [64, 64, 1],
		kernel_size = [3, 3, 1, 8],
		stride = 2
	)
	sw_stage_list.append(conv2d_1_stage)

	conv2d_2_stage = DNNProcessStage(
		name = "Conv2D_2",
		op_type = "Conv2D",
		ifmap_size = [32, 32, 8],
		kernel_size = [3, 3, 8, 16],
		stride = 2
	)
	sw_stage_list.append(conv2d_2_stage)

	conv2d_3_stage = DNNProcessStage(
		name = "Conv2D_3",
		op_type = "Conv2D",
		ifmap_size = [16, 16, 16],
		kernel_size = [3, 3, 16, 16],
		stride = 2
	)
	sw_stage_list.append(conv2d_3_stage)

	fc_1_stage = DNNProcessStage(
		name = "FC_1",
		op_type = "FC",
		ifmap_size = [1024, 1, 1],
		kernel_size = [1024, 256],
		stride = 1
	)
	sw_stage_list.append(fc_1_stage)

	fc_2_stage = DNNProcessStage(
		name = "FC_2",
		op_type = "FC",
		ifmap_size = [256, 1, 1],
		kernel_size = [256, 4],
		stride = 1
	)
	sw_stage_list.append(fc_2_stage)

	# encoder_decoder_stage = ProcessStage(
	# 	name = "EncoderDecoder",
	# 	input_size = [(256, 256, 1)],
	# 	output_size = (256, 256, 1)
	# )
	# sw_stage_list.append(encoder_decoder_stage)

	input_data = PixelInput((64, 64, 1), name="CurrInput")
	sw_stage_list.append(input_data)
	prev_input_data = PixelInput((64, 64, 1), name="PrevInput")
	sw_stage_list.append(prev_input_data)

	eventification_stage.set_input_stage(input_data)
	eventification_stage.set_input_stage(prev_input_data)

	# conv2d_1_stage.set_input_stage(edge_dectection_stage)
	conv2d_1_stage.set_input_stage(eventification_stage)

	conv2d_2_stage.set_input_stage(conv2d_1_stage)

	conv2d_3_stage.set_input_stage(conv2d_2_stage)

	conv2d_3_stage.flatten()
	# conv2d_3_stage = concat(conv2d_3_stage, bbox_find_stage)

	fc_1_stage.set_input_stage(conv2d_3_stage)
	fc_2_stage.set_input_stage(fc_1_stage)	

	# edge_dectection_stage.set_input_stage(encoder_decoder_stage)

	thresholding_stage.set_input_stage(fc_2_stage)
	thresholding_stage.set_input_stage(eventification_stage)

	
	# bbox_find_stage.set_input_stage(encoder_decoder_stage)

	# encoder_decoder_stage.set_input_stage(input_data)

	# conv2d_1_stage.set_input_stage(concat(edge_dectection_stage, eventification_stage))
	

	return sw_stage_list

if __name__ == '__main__':

	sw_stage_list = sw_pipeline()
	build_sw_graph(sw_stage_list)







