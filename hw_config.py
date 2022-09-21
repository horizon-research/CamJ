from pprint import pprint
import numpy as np

# import local modules
from enum_const import ProcessorLocation, ProcessDomain
from memory import Scratchpad
from hw_compute import ADC, ComputeUnit, SystolicArray
from mapping_file import mapping_function
from SW_pipeline import sw_pipeline, build_sw_graph


def hw_config():
    hw_dict = {
        "memory": [],
        "compute": []
    }

    in_sensor_buffer = Scratchpad(
        name="InSensorBuffer",
        size=(2, 8, 512 * 512 / 8),  # assume double buffer scratchpad with 8 banks each.
        # to store two 512x512 frames
        clock=500,  # MHz
        read_port=8,
        write_port=8,
        read_write_port=8,
        access_units=["EdgeDetection", "BBoxDetection", "Eventification", "Thresholding", "InSensorSystolicArray",
                      "OffchipBuffer", "ADC"],
        write_energy=3,
        read_energy=1,
        location=ProcessorLocation.COMPUTE_LAYER
    )
    hw_dict["memory"].append(in_sensor_buffer)

    offchip_buffer = Scratchpad(
        name="OffchipBuffer",
        size=(2, 16, 1024 * 64),  # assume double buffer scratchpad with 2MB size
        clock=500,  # MHz
        read_port=16,
        write_port=16,
        read_write_port=16,
        access_units=["InSensorBuffer", "NearSensorSystolicArray", "OffchipDRAM",
                      "EdgeDetection", "BBoxDetection"],
        write_energy=30,
        read_energy=10,

        location=ProcessorLocation.COMPUTE_LAYER
    )
    hw_dict["memory"].append(offchip_buffer)

    adc = ADC(
        name="ADC",
        type=1,  # this needs to be fixed, use some enum.
        pixel_adc_ratio=(1, 256, 1),
        output_throughput=(256, 1, 1),  # redundent
        location=ProcessorLocation.SENSOR_LAYER,
    )
    adc.set_output_buffer(offchip_buffer)
    hw_dict["compute"].append(adc)

    eventification_unit = ComputeUnit(
        name="Eventification",
        domain=ProcessDomain.DIGITAL,
        location=ProcessorLocation.SENSOR_LAYER,
        input_throughput=[(32, 1, 1), (32, 1, 1)],
        output_throughput=(32, 1, 1),
        clock=500,  # MHz
        energy=1,
        area=10,
        initial_delay=0,
        delay=1,
    )
    hw_dict["compute"].append(eventification_unit)

    eventification_unit.set_input_buffer(offchip_buffer)
    eventification_unit.set_output_buffer(in_sensor_buffer)

    thresholding_unit = ComputeUnit(
        name="Thresholding",
        domain=ProcessDomain.DIGITAL,
        location=ProcessorLocation.COMPUTE_LAYER,
        input_throughput=[(4, 1, 1), (4, 1, 1), (256, 256, 1)],
        output_throughput=(1, 1, 1),
        clock=500,  # MHz
        energy=1,
        area=10,
        initial_delay=0,
        delay=1,
    )
    hw_dict["compute"].append(thresholding_unit)

    thresholding_unit.set_input_buffer(in_sensor_buffer)
    thresholding_unit.set_output_buffer(in_sensor_buffer)

    in_sensor_dnn_acc = SystolicArray(
        name="InSensorSystolicArray",
        domain=ProcessDomain.DIGITAL,
        location=ProcessorLocation.COMPUTE_LAYER,
        size_dimension=(16, 16),
        clock=500,
        energy=16,
        area=160
    )
    hw_dict["compute"].append(in_sensor_dnn_acc)

    in_sensor_dnn_acc.set_input_buffer(in_sensor_buffer)
    in_sensor_dnn_acc.set_output_buffer(in_sensor_buffer)

    offchip_dnn_acc = SystolicArray(
        name="NearSensorSystolicArray",
        domain=ProcessDomain.DIGITAL,
        location=ProcessorLocation.OFF_CHIP,
        size_dimension=(32, 32),
        clock=500,
        energy=64,
        area=640
    )
    hw_dict["compute"].append(offchip_dnn_acc)

    offchip_dnn_acc.set_input_buffer(offchip_buffer)

    offchip_dnn_acc.set_output_buffer(offchip_buffer)

    edge_detection_unit = ComputeUnit(
        name="EdgeDetection",
        domain=ProcessDomain.DIGITAL,
        location=ProcessorLocation.OFF_CHIP,
        input_throughput=[(8, 8, 1)],
        output_throughput=(8, 8, 1),
        clock=500,  # MHz
        energy=1,
        area=5,
        initial_delay=2,
        delay=1,
    )
    hw_dict["compute"].append(edge_detection_unit)

    edge_detection_unit.set_input_buffer(offchip_buffer)
    edge_detection_unit.set_output_buffer(in_sensor_buffer)

    bbox_detection_unit = ComputeUnit(
        name="BBoxDetection",
        domain=ProcessDomain.DIGITAL,
        location=ProcessorLocation.OFF_CHIP,
        input_throughput=[(256, 256, 1)],
        output_throughput=(4, 1, 1),
        clock=500,  # MHz
        energy=1,
        area=15,
        initial_delay=0,
        delay=1
    )
    hw_dict["compute"].append(bbox_detection_unit)

    bbox_detection_unit.set_input_buffer(offchip_buffer)
    bbox_detection_unit.set_output_buffer(in_sensor_buffer)

    return hw_dict


# this function creates the mapping from sw stage to hw unit.
# sw stage to hw unit is one-to-one mapping. ???
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


def check_buffer_consistency(src_unit, dst_unit):
    if src_unit.output_buffer == dst_unit.input_buffer:
        return True
    else:
        raise Exception("%s %s don't have a common buffer to commnicate!" % src_unit.name, dst_unit.name)


def build_buffer_edges(sw_stage_list, hw_dict, sw2hw):
    buffer_edge_dict = {}

    for sw_stage in sw_stage_list:
        for output_stage in sw_stage.output_stages:
            src_unit = sw2hw[sw_stage]
            dst_unit = sw2hw[output_stage]
            print(src_unit, dst_unit)
            if check_buffer_consistency(src_unit, dst_unit):
                print("[edge]", src_unit, dst_unit, sw_stage, output_stage)
                buffer_edge_dict[src_unit, dst_unit] = src_unit.output_buffer
                dst_unit.set_input_hw_unit(sw_stage, src_unit)

    return buffer_edge_dict


def allocate_output_buffer(sw_stages, hw2sw, sw2hw, buffer_edge_dict):
    src_stages = []
    for sw_stage in sw_stages:
        for in_stage in sw_stage.input_stages:
            src_unit = sw2hw[in_stage]
            dst_unit = sw2hw[sw_stage]

            buffer = buffer_edge_dict[src_unit, dst_unit]
            print("buffer", buffer)
            print("reserve_buffer: ", src_unit, dst_unit, in_stage)
            buffer.reserve_buffer(
                src_hw_unit=src_unit,
                dst_hw_unit=dst_unit,
                sw_stage=in_stage,
                buffer_size=in_stage.output_size
            )

            if in_stage not in src_stages:
                src_stages.append(in_stage)

    for sw_stage in sw_stages:
        # this means that the sw stage is the last stage in the pipeline
        if sw_stage not in src_stages:
            src_unit = sw2hw[sw_stage]
            buffer = src_unit.output_buffer

            buffer.reserve_solo_buffer(
                src_hw_unit=src_unit,
                sw_stage=sw_stage,
                buffer_size=sw_stage.output_size
            )


def increment_buffer_index(buffer_index, buffer_size, throughput):
    new_buffer_index = np.zeros_like(buffer_index)
    if len(buffer_index) == 2:
        if throughput[0] + buffer_index[0] < buffer_size[0]:
            new_buffer_index[0] = throughput[0] + buffer_index[0]
            new_buffer_index[1] = buffer_index[1]
        elif throughput[1] + buffer_index[1] < buffer_size[1]:
            new_buffer_index[1] = throughput[1] + buffer_index[1]
            new_buffer_index[0] = 0
        else:
            new_buffer_index[1] = buffer_size[1]
            new_buffer_index[0] = buffer_size[0]
    elif len(buffer_index) == 3:
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

    return new_buffer_index


# this function check if one sw stage finishes writing the output.
# if finish, return true, otherwise, return false
def check_stage_finish(src_hw_unit, sw_stage, hw2sw):
    # get the output buffer index
    src_index = src_hw_unit.get_output_buffer_index(sw_stage)
    # find the output buffer, any sw_stage points to the same output buffer
    src_output_buffer = src_hw_unit.output_buffer

    # get the output buffer size
    output_buffer = src_output_buffer.reserved_buffer[src_hw_unit, sw_stage]
    output_buffer_shape = output_buffer.shape

    if len(output_buffer_shape) != len(src_index):
        raise Exception("the dimensions of Buffer size and source index are not matched.")
    else:
        num_element = 1
        for i in range(len(output_buffer_shape)):
            num_element = num_element * output_buffer_shape[i]
            if output_buffer_shape[i] != src_index[i]:
                return False

        sum_val = np.sum(output_buffer)
        if sum_val != num_element:
            print(np.where(output_buffer == 0))
            raise Exception("output buffer is not filled correctly!")

        return True


def find_index(src_index, buffer_shape, i, j, k):
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
    if z >= buffer_shape[2]:
        print("WARNING: [%d:%d:%d] is out of buffer size [%d:%d:%d]." % (
            x, y, z, buffer_shape[0], buffer_shape[1], buffer_shape[2]))

    return x, y, z


# write data to the output buffer, before call this funtion,
# make sure check if the input data for the source hw is ready.
def write_output_throughput(src_hw_unit, sw_stage, hw2sw):
    # find the output buffer, any sw_stage points to the same output buffer
    src_output_buffer = src_hw_unit.output_buffer

    # find the reserved buffer and buffer index
    print("## [write_output_throughput] ##", sw_stage, src_output_buffer.reserved_buffer[src_hw_unit, sw_stage].shape)
    src_index = src_hw_unit.get_output_buffer_index(sw_stage)
    src_output_throughput = src_hw_unit.output_throughput
    output_buffer = src_output_buffer.reserved_buffer[src_hw_unit, sw_stage]
    output_buffer_shape = output_buffer.shape
    print("## [write_output_throughput] ##", sw_stage, src_output_throughput, output_buffer_shape, src_index)
    if len(src_output_throughput) == 3:
        for i in range(src_output_throughput[0]):
            for j in range(src_output_throughput[1]):
                for k in range(src_output_throughput[2]):
                    x, y, z = find_index(src_index, output_buffer_shape, i, j, k)
                    if x < output_buffer_shape[0] and y < output_buffer_shape[1] and z < output_buffer_shape[2]:
                        output_buffer[x, y, z] = 1
    else:
        raise Exception("Non-implementation Error")

    new_buffer_index = increment_buffer_index(src_index, output_buffer_shape, src_output_throughput)
    print(src_index, new_buffer_index, src_output_throughput)
    src_hw_unit.set_output_buffer_index(sw_stage, new_buffer_index)


# this function is used to check if the input buffer has enough data to be consumed
# by the consumer unit.
def check_input_buffer_data_ready(dst_input_buffer, dst_input_throughput, dst_input_index):
    if len(dst_input_throughput) == 2:
        sum_val = np.sum(
            dst_input_buffer[
            dst_input_index[0]:dst_input_index[0] + dst_input_throughput[0],
            dst_input_index[1]:dst_input_index[1] + dst_input_throughput[1]
            ]
        )
        if sum_val == dst_input_throughput[0] * dst_input_throughput[1]:
            return True
        else:
            return False

    elif len(dst_input_throughput) == 3:
        sum_val = np.sum(
            dst_input_buffer[
            dst_input_index[0]:dst_input_index[0] + dst_input_throughput[0],
            dst_input_index[1]:dst_input_index[1] + dst_input_throughput[1],
            dst_input_index[2]:dst_input_index[2] + dst_input_throughput[2],
            ]
        )
        print("check data readiness:[",
              dst_input_index[0], ":", dst_input_index[0] + dst_input_throughput[0], ",",
              dst_input_index[1], ":", dst_input_index[1] + dst_input_throughput[1], ",",
              dst_input_index[2], ":", dst_input_index[2] + dst_input_throughput[2], "]")
        if sum_val == dst_input_throughput[0] * dst_input_throughput[1] * dst_input_throughput[2]:
            return True
        else:
            return False

    else:
        raise Exception("Hasn't been implemented yet!")


def increment_input_buffer_index(dst_hw_unit, sw_stage):
    # in this case, no producer dependency, return directly
    # no need to increment the input buffer index
    if dst_hw_unit.input_buffer is None:
        return

    dst_input_buffer = dst_hw_unit.input_buffer
    # print(dst_hw_unit, "has %d dependencies." % len(dst_hw_unit.input_throughput))
    # print("# ", dst_hw_unit, dst_hw_unit.input_hw_units)
    # print("input_throughput size", dst_hw_unit.input_throughput)
    # print(dst_hw_unit.input_index_list, sw_stage.input_stages)
    for i in range(len(dst_hw_unit.input_throughput)):
        print(sw_stage.input_stages)
        input_sw_stage = sw_stage.input_stages[i]
        src_hw_unit = dst_hw_unit.input_hw_units[input_sw_stage][0]
        dst_input_buffer = dst_hw_unit.input_buffer.reserved_buffer[src_hw_unit, input_sw_stage]
        dst_input_throughput = dst_hw_unit.input_throughput[i]
        dst_input_index = dst_hw_unit.get_input_buffer_index(src_hw_unit,
                                                             input_sw_stage)  # input_index_list[src_hw_unit, input_sw_stage]
        # increment the input buffer index
        new_dst_input_index = increment_buffer_index(dst_input_index, dst_input_buffer.shape, dst_input_throughput)
        # set the new index
        dst_hw_unit.set_input_buffer_index(src_hw_unit, input_sw_stage,
                                           new_dst_input_index)  # input_index_list[src_hw_unit, input_sw_stage] = new_dst_input_index
    return


def check_input_buffer(dst_hw_unit, sw_stage):
    # in this case, no producer dependency, return true directly
    if dst_hw_unit.input_buffer is None:
        print(dst_hw_unit, "has no dependencies and is ready")
        return True

    dst_input_buffer = dst_hw_unit.input_buffer
    print(dst_hw_unit, "has %d dependencies." % len(dst_hw_unit.input_throughput))
    print("# ", dst_hw_unit, dst_hw_unit.input_hw_units)
    print("input_throughput size", dst_hw_unit.input_throughput)
    print(dst_hw_unit.input_index_list, sw_stage.input_stages)
    for i in range(len(dst_hw_unit.input_throughput)):
        print(sw_stage.input_stages)
        input_sw_stage = sw_stage.input_stages[i]
        src_hw_unit = dst_hw_unit.input_hw_units[input_sw_stage][0]
        dst_input_buffer = dst_hw_unit.input_buffer.reserved_buffer[src_hw_unit, input_sw_stage]
        dst_input_throughput = dst_hw_unit.input_throughput[i]
        dst_input_index = dst_hw_unit.input_index_list[src_hw_unit, input_sw_stage]

        if not check_input_buffer_data_ready(dst_input_buffer, dst_input_throughput, dst_input_index):
            print(dst_hw_unit, "-> input sw_stage: ", input_sw_stage, "not ready")
            return False

        print(dst_hw_unit, ", input sw_stage: ", input_sw_stage, "ready")

    return True


class ReservationBoard(object):
    """docstring for ReservationBoard"""

    def __init__(self, hw_compute_units):
        super(ReservationBoard, self).__init__()
        self.occupation_board = {}
        self.reservation_board = {}
        for hw_unit in hw_compute_units:
            self.reservation_board[hw_unit] = False

    def check_reservation(self, hw_unit):
        if hw_unit in self.reservation_board:
            return self.reservation_board[hw_unit]
        else:
            raise Exception("%s is not in the reservation board" % hw_unit.name)

    def reserve_hw_unit(self, sw_stage, hw_unit):
        if self.reservation_board[hw_unit]:
            raise Exception("%s has already been reserved." % hw_unit.name)
        else:
            self.reservation_board[hw_unit] = True
            self.occupation_board[hw_unit] = sw_stage

    def reserve_by(self, sw_stage, hw_unit):
        # check if the hw_unit is reserved or not
        if not self.reservation_board[hw_unit]:
            return False
        # check if the occupied sw stage is the query sw stage
        if self.occupation_board[hw_unit] == sw_stage:
            return True
        else:
            return False

    def release_hw_unit(self, sw_stage, hw_unit):
        self.reservation_board[hw_unit] = False
        self.occupation_board.pop(hw_unit, None)


def main():
    hw_dict = hw_config()
    mapping_dict = mapping_function()
    sw_stage_list = sw_pipeline()
    reservation_board = ReservationBoard(hw_dict["compute"])

    build_sw_graph(sw_stage_list)

    sw2hw, hw2sw = map_sw_hw(mapping_dict, sw_stage_list, hw_dict)

    print("## [sw2hw] ##")
    pprint(sw2hw)

    print("## [hw2sw] ##")
    pprint(hw2sw)

    buffer_edge_dict = build_buffer_edges(sw_stage_list, hw_dict, sw2hw)

    print(buffer_edge_dict)

    allocate_output_buffer(
        sw_stages=sw_stage_list,
        hw2sw=hw2sw,
        sw2hw=sw2hw,
        buffer_edge_dict=buffer_edge_dict
    )

    # to check the correctness of the implementation
    # for sw_stage in sw_stage_list:
    # 	hw_stage = sw2hw[sw_stage]
    # 	print("[src hw stages]: ", hw_stage, sw_stage)
    # 	# pprint(hw_stage.input_hw_units)
    # 	pprint(hw_stage.output_buffer_size)
    # 	# pprint(hw_stage.output_index_list)

    # exit()

    finished_stage = {}
    processing_stage = {}

    for cycle in range(800000):
        print("\n\n#######  CYCLE %04d  ######" % cycle)
        for sw_stage in sw_stage_list:

            hw_unit = sw2hw[sw_stage]
            print("[== HW: ", hw_unit, ", SW: ", sw_stage)

            if sw_stage in finished_stage:
                print(sw_stage, "is finished already")
                continue

            # this will check if a sw stage is already into computing phase,
            # wait for the compute to be finished
            if sw_stage in processing_stage:
                hw_unit.process_one_cycle()
                check_input_buffer(hw_unit, sw_stage)
                if hw_unit.finish_computation():
                    # output data to the targeted buffer and increment output buffer index
                    write_output_throughput(hw_unit, sw_stage, hw2sw)
                    # if the computation is finished, remove the sw stage from processing stage list
                    processing_stage.pop(sw_stage)
                    if check_stage_finish(hw_unit, sw_stage, hw2sw):
                        print("## ", sw_stage, "finish writing the buffer.", hw_unit, "is released.")
                        reservation_board.release_hw_unit(sw_stage, hw_unit)
                        finished_stage[sw_stage] = True
            elif check_input_buffer(hw_unit, sw_stage):
                # if the hw unit is not occupied by any sw stage, reserve the hw unit
                if not reservation_board.check_reservation(hw_unit):
                    print("HW: ", hw_unit, "is available.")
                    # reserve the hw unit first
                    reservation_board.reserve_hw_unit(sw_stage, hw_unit)
                    # increment the input buffer index
                    increment_input_buffer_index(hw_unit, sw_stage)
                    hw_unit.init_elapse_cycle()
                    processing_stage[sw_stage] = True
                # # output data to the targeted buffer and increment output buffer index
                # write_output_throughput(hw_unit, sw_stage, hw2sw)
                # if check_stage_finish(hw_unit, sw_stage, hw2sw):
                # 	print("## ", sw_stage, "finish writing the buffer.", hw_unit, "is released.")
                # 	reservation_board.release_hw_unit(sw_stage, hw_unit)
                # 	finished_stage[sw_stage] = True
                elif reservation_board.reserve_by(sw_stage, hw_unit):
                    # increment the input buffer index
                    increment_input_buffer_index(hw_unit, sw_stage)
                    hw_unit.init_elapse_cycle()
                    processing_stage[sw_stage] = True
                # # output data to the targeted buffer and increment output buffer index
                # write_output_throughput(hw_unit, sw_stage, hw2sw)
                # if check_stage_finish(hw_unit, sw_stage, hw2sw):
                # 	print("## ", sw_stage, "finish writing the buffer.", hw_unit, "is released.")
                # 	reservation_board.release_hw_unit(sw_stage, hw_unit)
                # 	finished_stage[sw_stage] = True
                else:
                    print("HW: ", hw_unit, "is not available.")

        print("[Finished stage]: ", finished_stage)
        if len(finished_stage.keys()) == len(sw_stage_list):
            print("DONE!")
            exit()


if __name__ == '__main__':
    main()
