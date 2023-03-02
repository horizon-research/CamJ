'''
    This file includes important functions that are used in simulation.
    Those function are the logic in the simulation and intentionally hidden from the users.

'''

import numpy as np
from camj.sim_core.digital_memory import FIFO, LineBuffer
from camj.sim_core.sw_interface import ProcessStage, DNNProcessStage
from camj.sim_core.flags import *

# this function creates the mapping from sw stage to hw unit.
# sw stage to hw unit is one-to-one mapping.
# hw unit to sw stage is one-to-multi mapping.
def map_sw_hw(mapping_dict, sw_stage_list, hw_dict):
    sw2hw = {}
    hw2sw = {}
    for k, v in mapping_dict.items():
        sw = None
        for sw_stage in sw_stage_list:
            if sw_stage.name == k:
                sw = sw_stage
                break

        hw = None
        for hw_unit in hw_dict["compute"]:
            if hw_unit.name == v:
                hw = hw_unit
                break

        if hw != None and sw != None:
            sw2hw[sw] = hw
            if hw in hw2sw:
                hw2sw[hw].append(sw)
            else:
                hw2sw[hw] = [sw]

    return sw2hw, hw2sw

def find_digital_sw_stages(sw_stages, compute_units, mapping_dict):
    digital_sw_stages = []

    for sw_stage in sw_stages:
        hw_stage_name = mapping_dict[sw_stage.name]

        for compute_unit in compute_units:
            if compute_unit.name == hw_stage_name:
                digital_sw_stages.append(sw_stage)
                break

    return digital_sw_stages

'''
    This function is used to double check if the producer's output buffer is the same as 
    the cosumer's input buffer.
    This function is used after the computation graph is constructed.

'''
def check_buffer_consistency(src_unit, dst_unit):

    if src_unit.output_buffer == dst_unit.input_buffer:
        return True
    else:
        raise Exception("%s %s don't have a common buffer to commnicate!" % (src_unit.name, dst_unit.name))

'''
    This function is used to connect the consumer and producer in the computational graph.
'''
def build_buffer_edges(sw_stage_list, hw_dict, sw2hw):

    buffer_edge_dict = {}

    for sw_stage in sw_stage_list:
        for output_stage in sw_stage.output_stages:
            src_unit = sw2hw[sw_stage]
            dst_unit = sw2hw[output_stage]
            # print(src_unit, dst_unit)
            if check_buffer_consistency(src_unit, dst_unit):
                buffer_edge_dict[src_unit, dst_unit] = src_unit.output_buffer
                dst_unit.set_input_hw_unit(sw_stage, src_unit)

    return buffer_edge_dict

def calculate_virtual_size(dst_stage, src_stage):
    if isinstance(dst_stage, ProcessStage):
        kernel_size = dst_stage.kernel_size
        output_size = src_stage.output_size
        if dst_stage.padding[0]:
            return (
                output_size[0]+2*(kernel_size[0][0]//2),
                output_size[1]+2*(kernel_size[0][1]//2),
                output_size[2]+2*(kernel_size[0][2]//2)
            )
        else:
            return (
                output_size[0],
                output_size[1],
                output_size[2]
            )
    else:
        return src_stage.output_size
'''
    Allocate actual buffer for each producer-consumer pair, this function is used to
    check the progress of each compute stage and perform sanity check after each computation.
'''
def allocate_output_buffer(sw_stages, hw2sw, sw2hw, buffer_edge_dict):
    src_stages = []
    for sw_stage in sw_stages:
        for in_stage in sw_stage.input_stages:
            # find producer and consumer HW.
            src_unit = sw2hw[in_stage]
            dst_unit = sw2hw[sw_stage]
            # find buffer.
            buffer = buffer_edge_dict[src_unit, dst_unit]
            if ENABLE_DEBUG:
                print(
                    "[allocate_output_buffer] reserve_buffer: ", buffer, 
                    ", src:", src_unit, ", dst:", dst_unit, ", stage:", in_stage)
            virtual_size = calculate_virtual_size(sw_stage, in_stage)
            if ENABLE_DEBUG:
                print("[allocate_output_buffer] virtual_size: ", virtual_size)
            # allocate a buffer size as the same size of the output dimension.
            buffer.reserve_buffer(
                src_hw_unit = src_unit, 
                dst_hw_unit = dst_unit, 
                sw_stage = in_stage,
                buffer_size = in_stage.output_size,
                virtual_size = virtual_size
            )
            # append input stage to the src_stage list. This will be used to find the final stage.
            # Final stage: only serves as producer and no corresponding consumer HW unit.
            if in_stage not in src_stages:
                src_stages.append(in_stage)

    # allocate buffer for the final stage.
    for sw_stage in sw_stages:
        # this means that the sw stage is the last stage in the pipeline
        if sw_stage not in src_stages:
            src_unit = sw2hw[sw_stage]
            buffer = src_unit.output_buffer
            if ENABLE_DEBUG:
                print(
                    "[allocate_output_buffer] reserve_solo_buffer: ", buffer, 
                    "stage:", sw_stage, "size: ", sw_stage.output_size
                )

            buffer.reserve_solo_buffer(
                src_hw_unit = src_unit, 
                sw_stage = sw_stage, 
                buffer_size = sw_stage.output_size
            )

'''
    This function is used to calculate the next index for both input buffer and output buffer.
'''
def increment_buffer_index(buffer_index, buffer_size, throughput):
    new_buffer_index = np.zeros_like(buffer_index)
    if len(buffer_index) == 3:
        if throughput[0] + buffer_index[0] < buffer_size[0]:
            new_buffer_index[0] = throughput[0] + buffer_index[0]
            new_buffer_index[1] = buffer_index[1]
            new_buffer_index[2] = buffer_index[2]
        elif throughput[1] + buffer_index[1] < buffer_size[1]:
            new_buffer_index[1] = throughput[1] + buffer_index[1]
            new_buffer_index[0] = 0
            new_buffer_index[2] = buffer_index[2]
        elif throughput[2] + buffer_index[2] < buffer_size[2]:
            new_buffer_index[2] = throughput[2] + buffer_index[2]
            new_buffer_index[0] = 0
            new_buffer_index[1] = 0
        else:
            new_buffer_index[0] = buffer_size[0]        
            new_buffer_index[1] = buffer_size[1]
            new_buffer_index[2] = buffer_size[2]

    else:
        raise Exception("Fail to increment buffer index, buffer index size needs to be 3.")

    return new_buffer_index

'''
    This function check if one sw stage finishes writing the output.
    If finish, return true, otherwise, return false
'''
def check_stage_finish(src_hw_unit, sw_stage, hw2sw):
    # get the output buffer index
    src_index = src_hw_unit.get_output_buffer_index(sw_stage)
    # find the output buffer, any sw_stage points to the same output buffer
    src_output_buffer = src_hw_unit.output_buffer

    # get the output buffer size
    output_buffer = src_output_buffer.reserved_buffer[src_hw_unit, sw_stage]
    output_buffer_shape =src_hw_unit.get_output_buffer_size(sw_stage)

    if len(output_buffer_shape) != len(src_index):
        raise Exception("the dimensions of Buffer size and source index are not matched.")
    else:
        num_element = 1
        for i in range(len(output_buffer_shape)):
            num_element = num_element * output_buffer_shape[i]
            if output_buffer_shape[i] != src_index[i]:
                return False

        if ENABLE_DEBUG:
            print("[check_stage_finish]: ", output_buffer.shape, src_index)
        sum_val = np.sum(output_buffer[:output_buffer_shape[0], :output_buffer_shape[1], :output_buffer_shape[2]])
        # print(sum_val, num_element)
        if sum_val != num_element:
            # print(np.where(output_buffer == 0))
            raise Exception("output buffer is not filled correctly!")

        return True

'''
    To calculate the next index to access. The access pattern is row-major.
    This function takes care of carrying, e.g. x+i exceeds the x dimension.
    src_index: the base index (x, y, z).
    i: the increment amount in x-axis.
    j: the increment amount in y-axis.
    k: the increment amount in z-axis.
'''
def calc_index(src_index, buffer_shape, i, j, k):
    x = src_index[0] + i
    carry = 0
    if x >= buffer_shape[0]:
        carry = 1
        x = x - buffer_shape[0]

    y = src_index[1] + carry + j
    carry = 0
    if y >= buffer_shape[1]:
        carry = 1
        y = y - buffer_shape[1]

    z = src_index[2] + carry + k
    # if z >= buffer_shape[2]:
    #   # print(
    #   #   "WARNING: [%d:%d:%d] is out of buffer size [%d:%d:%d]." % \
    #   #   (x, y, z, buffer_shape[0], buffer_shape[1], buffer_shape[2])
    #   # )

    return x, y, z
'''
    write data to the output buffer, before call this funtion,
    make sure check if the input data for the source hw is ready.
'''
def write_output_throughput(src_hw_unit, sw_stage, hw2sw, write_index, write_cnt):
    # find the output buffer, any sw_stage points to the same output buffer
    src_output_buffer = src_hw_unit.output_buffer
    
    # find the reserved buffer and buffer index
    src_index = src_hw_unit.get_output_buffer_index(sw_stage)
    src_output_throughput = src_hw_unit.output_per_cycle
    output_buffer = src_output_buffer.reserved_buffer[src_hw_unit, sw_stage]
    output_buffer_shape = src_hw_unit.get_output_buffer_size(sw_stage)
    if ENABLE_DEBUG:
        print(
            "[write_output_throughput]", sw_stage, 
            "src_output_per_cycle:", src_output_throughput, 
            "src_index:", src_index,
            "output_buffer_shape:", output_buffer_shape
        )

    idx = 0
    # mark each output element in the output buffer. Change value from 0 to 1
    if len(src_output_throughput) == 3:
        for i in range(src_output_throughput[0]):
            for j in range(src_output_throughput[1]):
                for k in range(src_output_throughput[2]):
                    x, y, z = calc_index(src_index, output_buffer_shape, i, j, k)
                    if idx >= write_index and idx < write_index + write_cnt:
                        # ignore the index out of bound.
                        if x < output_buffer_shape[0] and y < output_buffer_shape[1] and z < output_buffer_shape[2]:
                            output_buffer[x, y, z] = 1
                            # print("x, y, z: ", x, y, z)

                    idx += 1
    else:
        raise Exception("Non-implementation Error, throughput shape size needs to be 3.")

    # this finds the new buffer index for next compute.
    if write_index + write_cnt >= idx:
        new_buffer_index = increment_buffer_index(src_index, output_buffer_shape, src_output_throughput)
        if ENABLE_DEBUG:
            print(
                "[write_output_per_cycle]", "src_index: ", src_index, 
                "new_src_index: ", new_buffer_index, 
                "src_output_per_cycle: ", src_output_throughput
            )
            
        # set the new buffer index.
        src_hw_unit.set_output_buffer_index(sw_stage, new_buffer_index)

'''
    This function is used to check if the input buffer has enough data to be consumed
    by the consumer unit.
    e.g. for a 3x3 Conv ops. it checks that if there is a new batch of 3x3 data in input buffer.
'''
def check_input_buffer_data_ready(dst_input_buffer, dst_input_throughput, dst_input_index):
    if len(dst_input_throughput) == 3:
        sum_val = np.sum(
            dst_input_buffer[
                dst_input_index[0]:dst_input_index[0]+dst_input_throughput[0],
                dst_input_index[1]:dst_input_index[1]+dst_input_throughput[1],
                dst_input_index[2]:dst_input_index[2]+dst_input_throughput[2],
            ]
        )
        if ENABLE_DEBUG:
            print("[check_input_buffer_data_ready] [dst_input_curr_index : +input per_cycle] --> [", 
                  dst_input_index[0], ":", dst_input_index[0] + dst_input_throughput[0], ",",
                  dst_input_index[1], ":", dst_input_index[1] + dst_input_throughput[1], ",",
                  dst_input_index[2], ":", dst_input_index[2] + dst_input_throughput[2], "]")
            print("[check_input_buffer_data_ready] sum val: ", sum_val)
        if sum_val == dst_input_throughput[0] * dst_input_throughput[1] * dst_input_throughput[2]:
            return True
        else:
            return False

    else:
        raise Exception("check_input_buffer_data_ready: throughput size is not 3 yet!")

def scale_input_throughput(input_throughput, input_kernel, input_stride, input_index, input_size):
    flag = True
    ret_throughput = []
    for i in range(len(input_throughput)):
        if flag and input_index[i] + input_throughput[i] == input_size[i]:
            ret_throughput.append(int(input_throughput[i]))
        else:
            flag = False
            if i == 1:
                ret_throughput.append(int(input_throughput[i]/input_kernel[i]*input_stride[i]))
            else:
                ret_throughput.append(int(input_throughput[i]))

    return ret_throughput

'''
    increment the input buffer index, the input buffer index needs to be incremented before fetching
    the next batch of data.
'''
def increment_input_buffer_index(dst_hw_unit, sw_stage):
    # in this case, no producer dependency, return directly
    # no need to increment the input buffer index
    if dst_hw_unit.input_buffer is None:
        return
    is_line_buffer = isinstance(dst_hw_unit.input_buffer, LineBuffer)
    if ENABLE_DEBUG:
        print("[increment_input_buffer_index] dst hw unit: ", dst_hw_unit, "sw_stage: ", sw_stage)

    # needs to increment index for each input throughput
    for i in range(len(dst_hw_unit.input_per_cycle)):
        input_sw_stage = sw_stage.input_stages[i]
        input_size = sw_stage.input_size[i]
        input_kernel = sw_stage.kernel_size[i]
        input_stride = sw_stage.stride[i]

        if ENABLE_DEBUG:
            print("[increment_input_buffer_index] input sw stage: ", input_sw_stage)
            print("[increment_input_buffer_index] input size: ", input_size)
            print("[increment_input_buffer_index] input kernel: ", input_kernel, "input stride: ", input_stride)

        # 0 here is to find the first one item in the list,
        # the list is always a length of 1 list.
        src_hw_unit = dst_hw_unit.input_hw_units[input_sw_stage][0]

        dst_input_buffer = dst_hw_unit.input_buffer.reserved_buffer[src_hw_unit, input_sw_stage]
        dst_input_throughput = dst_hw_unit.input_per_cycle[i]
        # get the previous input index
        dst_input_index = dst_hw_unit.get_input_buffer_index(src_hw_unit, input_sw_stage)

        if ENABLE_DEBUG:
            print("[increment_input_buffer_index] src hw unit: ", src_hw_unit, "dst_input_buffer: ", dst_input_buffer.shape)
            print("[increment_input_buffer_index] dst_input_throughput: ", dst_input_throughput, "dst_input_index: ", dst_input_index)
        
        if is_line_buffer:
            dst_input_throughput = scale_input_throughput(
                dst_input_throughput, 
                input_kernel,
                input_stride, 
                dst_input_index, 
                input_size
            )
        
        # increment the input buffer index
        new_dst_input_index = increment_buffer_index(
            dst_input_index, 
            dst_input_buffer.shape, 
            dst_input_throughput,

        )
        # set the new index
        if ENABLE_DEBUG:
            print(
                "[increment_input_buffer_index]", sw_stage, 
                "previous input index: ", dst_input_index, 
                "new input index", new_dst_input_index,
                "dst_input_throughput: ", dst_input_throughput
            )
        dst_hw_unit.set_input_buffer_index(src_hw_unit, input_sw_stage, new_dst_input_index)
    return

'''
    Check for this particular SW stage, if the input data are ready.    
'''
def check_input_buffer(dst_hw_unit, sw_stage):
    # in this case, no producer dependency, return true directly
    if dst_hw_unit.input_buffer is None:
        if ENABLE_DEBUG:
            print("[check_input_buffer]", dst_hw_unit, "has no dependencies and is ready")
        return True

    dst_input_buffer = dst_hw_unit.input_buffer
    if ENABLE_DEBUG:
        print("[check_input_buffer]", dst_hw_unit, "has %d dependencies." % len(dst_hw_unit.input_per_cycle))
        print("[check_input_buffer]", dst_hw_unit, dst_hw_unit.input_hw_units)
        print("input_per_cycle size", dst_hw_unit.input_per_cycle)
        print("[check_input_buffer]", dst_hw_unit.input_index_list, sw_stage.input_stages)
    for i in range(len(dst_hw_unit.input_per_cycle)):
        input_sw_stage = sw_stage.input_stages[i]
        src_hw_unit = dst_hw_unit.input_hw_units[input_sw_stage][0]
        dst_input_buffer = dst_hw_unit.input_buffer.reserved_buffer[src_hw_unit, input_sw_stage]
        dst_input_throughput = dst_hw_unit.input_per_cycle[i]
        dst_input_index = dst_hw_unit.input_index_list[src_hw_unit, input_sw_stage]

        if not check_input_buffer_data_ready(dst_input_buffer, dst_input_throughput, dst_input_index):
            return False

    return True

def check_fc_input_ready(sw_stage, finished_stage):
    for input_stage in sw_stage.input_stages:
        if not input_stage in finished_stage:
            return False

    return True

def check_finish_data_dependency(sw_stage, finished_stage):
    for input_stage in sw_stage.input_stages:
        if input_stage not in finished_stage:
            raise Exception(
                "[CHECK FAIL] %s's input stage, %s, is not finished. failed the data dependency" \
                % (sw_stage.name, input_stage.name)
            )

def check_input_stage_finish(sw_stage, finished_stage):
    for in_stage in sw_stage.input_stages:
        if in_stage not in finished_stage:
            return False

    return True
