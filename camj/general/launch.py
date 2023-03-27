import copy
from pprint import pprint
from prettytable import PrettyTable
import numpy as np
from inspect import signature

# import local modules
from camj.analog.utils import _find_analog_sw_stages, _find_analog_sw_mapping, analog_energy_simulation
from camj.digital.compute import SystolicArray, SIMDProcessor
from camj.digital.infra import ReservationBoard, BufferMonitor
from camj.digital.utils import map_sw_hw, check_buffer_consistency, build_buffer_edges, \
                    allocate_output_buffer, increment_buffer_index, check_stage_finish, \
                    write_output_throughput, check_input_buffer_data_ready, \
                    increment_input_buffer_index, check_input_buffer, check_finish_data_dependency, \
                    check_input_stage_finish, find_digital_sw_stages
from camj.general.enum import ProcessorLocation, ProcessDomain
from camj.general.flags import *
from camj.sw.interface import PixelInput
from camj.sw.utils import build_sw_graph

 
def energy_simulation(hw_desc, mapping, sw_desc):
    """Launch Energy Simulation

    The overall harness function to simulate analog and digital computation.

    Args:
        hw_desc (dict): hardware description.
        mapping (dict): mapping between software stages and hardware structures.
        sw_desc (list): software pipeline list.
    """
    # deep copy in case the function modify the orginal data
    hw_dict = copy.deepcopy(hw_desc)
    mapping_dict = copy.deepcopy(mapping)
    sw_stage_list = copy.deepcopy(sw_desc)
    print("###  Launch analog simulation  ###")
    analog_energy_dict = analog_energy_simulation(hw_dict["analog"], sw_stage_list, mapping_dict)

    print("\n###  Launch digital simulation  ###")
    digital_energy_dict = digital_energy_simulation(hw_dict, mapping_dict, sw_stage_list)

    ret_energy_dict = {}
    print_tab = PrettyTable(["Component Name", "Energy (pJ)"])
    total_energy = 0
    for name in analog_energy_dict.keys():
        ret_energy_dict[name] = analog_energy_dict[name]
        total_energy += analog_energy_dict[name]
        print_tab.add_row([name, analog_energy_dict[name]])

    for name in digital_energy_dict.keys():
        ret_energy_dict[name] = digital_energy_dict[name]
        total_energy += digital_energy_dict[name]
        print_tab.add_row([name, digital_energy_dict[name]])

    print("\nTotal energy: ", total_energy, "pJ")
    print("Energy breakdown:")
    print(print_tab)

    return total_energy, ret_energy_dict


def digital_energy_simulation(hw_desc, mapping, sw_desc):
    """Launch Digital Simulation

    The function to simulate digital computation.

    Args:
        hw_desc (dict): hardware description.
        mapping (dict): mapping between software stages and hardware structures.
        sw_desc (list): software pipeline list.
    """
    # some infras for digital simulation
    reservation_board = ReservationBoard(hw_desc["compute"])
    # find software stages that are only in digital simulation
    sw_stage_list = find_digital_sw_stages(sw_desc, hw_desc["compute"], mapping)

    if len(sw_stage_list) == 0:
        print("[DIGITAL] No software stages are mapped to digital domain.\n")
        return {}

    # find interface stages
    sw_stage_list, mapping_dict = _find_analog_interface_stages(
        sw_stage_list, 
        sw_desc, 
        mapping
    )

    # this function will build the connection between input stage and output stage.
    build_sw_graph(sw_stage_list)

    sw2hw, hw2sw = map_sw_hw(mapping_dict, sw_stage_list, hw_desc)

    buffer_edge_dict = build_buffer_edges(sw_stage_list, hw_desc, sw2hw)

    allocate_output_buffer(
        sw_stages = sw_stage_list,
        hw2sw = hw2sw, 
        sw2hw = sw2hw, 
        buffer_edge_dict = buffer_edge_dict
    )

    # initialize different stage list
    idle_stage = {}
    writing_stage = {}
    reading_stage = {}
    processing_stage = {}
    finished_stage = {}
    reserved_cycle_cnt = {}

    # initialize every stage to idle stage
    for sw_stage in sw_stage_list:
        idle_stage[sw_stage] = True

    for cycle in range(MAX_CYCLE_CNT):
        if cycle % PRINT_CYCLE == 0:
            print("\n\n#######  CYCLE %04d  ######" % cycle)

        # iterate each sw_stage
        for sw_stage in sw_stage_list:
            hw_unit = sw2hw[sw_stage]
            if cycle % PRINT_CYCLE == 0:
                print("[ITERATE] HW: ", hw_unit, ", SW: ", sw_stage)

            if sw_stage in finished_stage:
                if cycle % PRINT_CYCLE == 0:
                    print("[FINISH]", sw_stage, "is finished already")
                continue

            if sw_stage in reserved_cycle_cnt:
                reserved_cycle_cnt[sw_stage] += 1

            # check if the sw stage is in reading phase
            if sw_stage in reading_stage:
                if cycle % PRINT_CYCLE == 0:
                    print("[READ]", sw_stage, "in reading stage")
                # find input buffer and remaining amount of data need to be read
                input_buffer = hw_unit.input_buffer
                remain_read_cnt = hw_unit._num_read_remain()
                if cycle % PRINT_CYCLE == 0:
                    print("[READ]", "[HW unit : SW stage]", hw_unit, sw_stage, "Input Buffer: ", input_buffer)
                # this means that this hw_unit doesn't have data dependencies.
                if remain_read_cnt == 0:
                    if cycle % PRINT_CYCLE == 0:
                        print("[READ]", hw_unit, "is ready to compute, no data dependencies")
                    # refresh the compute status in hw_unit
                    hw_unit._init_elapse_cycle()
                    processing_stage[sw_stage] = True
                    reading_stage.pop(sw_stage)

                # check if there is any data can be read from buffer
                elif input_buffer._have_data_read(remain_read_cnt):
                    input_buffer._read_data(remain_read_cnt)
                    hw_unit._read_from_input_buffer(remain_read_cnt)
                    if hw_unit._check_read_finish():
                        if cycle % PRINT_CYCLE == 0:
                            print("[READ]", hw_unit, "is ready to compute")
                        # refresh the compute status in hw_unit
                        hw_unit._init_elapse_cycle()
                        processing_stage[sw_stage] = True
                        reading_stage.pop(sw_stage)
                # here to check if all input stages are finished, if so, this stage uses zero paddings
                elif check_input_stage_finish(sw_stage, finished_stage):
                    hw_unit._read_from_input_buffer(remain_read_cnt)
                    if hw_unit._check_read_finish():
                        if cycle % PRINT_CYCLE == 0:
                            print("[READ]", hw_unit, "is ready to compute, previous stage is finished.")
                        # refresh the compute status in hw_unit
                        hw_unit._init_elapse_cycle()
                        processing_stage[sw_stage] = True
                        reading_stage.pop(sw_stage)
                else:
                    if cycle % PRINT_CYCLE == 0:
                        print("READ", input_buffer, "input_buffer have no new data to read")


            # this will check if a sw stage is already into computing phase,
            # wait for the compute to be finished
            if sw_stage in processing_stage:
                if cycle % PRINT_CYCLE == 0:
                    print("[PROCESS]", sw_stage, "in processing_stage")
                hw_unit._process_one_cycle()
                # check_input_buffer(hw_unit, sw_stage)
                if hw_unit._finish_computation():
                    # # output data to the targeted buffer and increment output buffer index
                    # write_output_throughput(hw_unit, sw_stage, hw2sw)

                    # if the computation is finished, remove the sw stage from processing stage list
                    # add sw_stage to writing stage
                    writing_stage[sw_stage] = True
                    processing_stage.pop(sw_stage)

            # This check the writing stage. 
            # First, check if there is any data to write,
            # Second, check if there is any avialble ports in current cycle, 
            # if yes, request port and write data.
            if sw_stage in writing_stage:
                if cycle % PRINT_CYCLE == 0:
                    print("[WRITE]", sw_stage, "in writing stage")
                output_buffer = hw_unit.output_buffer
                remain_write_cnt = hw_unit._num_write_remain()
                if cycle % PRINT_CYCLE == 0:
                    print("[WRITE]", "[HW unit : SW stage]", hw_unit, sw_stage, "Output Buffer: ", output_buffer)
                # this means that this hw_unit doesn't have any output data.
                if remain_write_cnt == 0:
                    if cycle % PRINT_CYCLE == 0:
                        print("[WRITE]", hw_unit, "has no output data.")
                    # set sw_stage to idle stage
                    idle_stage[sw_stage] = True
                    writing_stage.pop(sw_stage)

                # then, check if there is any space to write
                elif output_buffer._have_space_to_write(remain_write_cnt):
                    output_buffer._write_data(remain_write_cnt)
                    write_index = hw_unit._write_to_output_buffer(remain_write_cnt)
                    # output data to the targeted buffer and increment output buffer index
                    write_output_throughput(hw_unit, sw_stage, hw2sw, write_index, remain_write_cnt)
                    if hw_unit._check_write_finish():
                        if cycle % PRINT_CYCLE == 0:
                            print("[WRITE]", hw_unit, "finishes writing")
                        # set sw_stage to idle stage
                        idle_stage[sw_stage] = True
                        writing_stage.pop(sw_stage)
                else:
                    if cycle % PRINT_CYCLE == 0:
                        print("[WRITE]", output_buffer, "have no space to write")
                        exit()

                if check_stage_finish(hw_unit, sw_stage, hw2sw):
                    if cycle % PRINT_CYCLE == 0:
                        print("[WRITE]", sw_stage, "finish writing the buffer.", hw_unit, "is released.")
                    reservation_board.release_hw_unit(sw_stage, hw_unit)
                    finished_stage[sw_stage] = True
                    # also need to pop sw_stage from the idle stage
                    idle_stage.pop(sw_stage)
                    # check if all input stages of sw_stage have been finished,
                    # this is used to check if there is data dependency is correct
                    check_finish_data_dependency(sw_stage, finished_stage)


            # check if the sw stage is in idle phase
            if sw_stage in idle_stage:
                # this check is to help to config the systolic array into correct configuration
                # before checking the data readiness.
                # Otherwise, there can be some infinite checkings in the program due to incorrect
                # systolic array configuration.
                if not reservation_board.check_reservation(hw_unit):
                    # check if the hw unit is a systolic array instance or SIMD processor,
                    # if yes, needs to modify the input/output throughput.
                    if isinstance(hw_unit, SystolicArray) or isinstance(hw_unit, SIMDProcessor):
                        hw_unit._config_throughput(
                            sw_stage.ifmap_size, 
                            sw_stage.output_size,
                            sw_stage.stride[0],
                            sw_stage.kernel_size[0],
                            sw_stage.op_type
                        )

                # first to check if the input buffer contains the data
                if check_input_buffer(hw_unit, sw_stage) or check_input_stage_finish(sw_stage, finished_stage):
                    if cycle % PRINT_CYCLE == 0:
                        print("[IDLE]", sw_stage, "in idle stage, input data ready")
                    # if the hw unit is not occupied by any sw stage, reserve the hw unit
                    if not reservation_board.check_reservation(hw_unit):
                        if cycle % PRINT_CYCLE == 0:
                            print("[IDLE]", sw_stage, "request --> HW: ", hw_unit, "is available.")
                        # reserve the hw unit first
                        reservation_board.reserve_hw_unit(sw_stage, hw_unit)
                        reserved_cycle_cnt[sw_stage] = 0
                        
                        hw_unit._start_init_delay()
                        # increment the input buffer index
                        increment_input_buffer_index(hw_unit, sw_stage)
                        reading_stage[sw_stage] = True
                        idle_stage.pop(sw_stage)
                    elif reservation_board.reserve_by(sw_stage, hw_unit):
                        # increment the input buffer index
                        increment_input_buffer_index(hw_unit, sw_stage)
                        reading_stage[sw_stage] = True
                        idle_stage.pop(sw_stage)
                    else:
                        if cycle % PRINT_CYCLE == 0:
                            print("[IDLE] HW: ", hw_unit, "is not available.")
                else:
                    if cycle % PRINT_CYCLE == 0:
                        print("[IDLE]", sw_stage, "in idle stage, input data NOT ready")

        if cycle % PRINT_CYCLE == 0:                
            print("[Finished stage]: ", finished_stage)

        if len(finished_stage.keys()) == len(sw_stage_list):
            hw_list = hw_desc["compute"]
            print("\n\n[Summary]")
            print("Overall system cycle count: ", cycle)
            print("[Cycle distribution]", reserved_cycle_cnt)
            ret_dict = {}
            for hw_unit in hw_list:
                ret_dict[hw_unit.name] = hw_unit.compute_energy()
                print(hw_unit, 
                    "total compute cycle: ", hw_unit.sys_all_compute_cycle,
                    "total compute energy: %d pJ" % hw_unit.compute_energy())

            for mem_unit in hw_desc["memory"]:
                print(mem_unit, "total memory energy: %d pJ" % mem_unit.total_memory_access_energy())

            print("[End] Digitial Simulation is DONE!")
            return ret_dict
            

    print("\nSimulation is not finished, increase your cycle counts or debug your code.")


def functional_simulation(sw_desc, hw_desc, mapping, input_mapping):
    """Launch Functional Simulation

    The function to simulate functional computation.

    Args:
        hw_desc (dict): hardware description.
        mapping (dict): mapping between software stages and hardware structures.
        sw_desc (list): software pipeline list.
        input_mapping (dict): input data mapping.
    """
    # deep copy in case the function modify the orginal data
    hw_dict = copy.deepcopy(hw_desc)
    mapping_dict = copy.deepcopy(mapping)
    sw_stage_list = copy.deepcopy(sw_desc)
    # complete the software stages data dependency graph.
    build_sw_graph(sw_stage_list)

    # find software stages that are computed in analog domain
    analog_sw_stages = _find_analog_sw_stages(sw_stage_list, hw_dict["analog"], mapping_dict)
    analog_sw_mapping = _find_analog_sw_mapping(sw_stage_list, hw_dict["analog"], mapping_dict)

    finished_stages = []
    ready_input = {}
    visited_analog_array = []
    simulation_res = {}
    # first process those analog stages that are initial stage in analog pipeline.
    for k in input_mapping.keys():
        analog_array = analog_sw_mapping[k]

        # if no input array, then it is the source, perform noise modeling
        if len(analog_array.input_arrays) == 0:
            noise_res_list = analog_array.noise(input_mapping[k])
            for pair in noise_res_list:
                simulation_res[pair[0]] = pair[1]
            ready_input[k] = noise_res_list[-1][1]
            finished_stages.append(k)
            visited_analog_array.append(analog_array)
        # if this analog array has any input array, then, this is just part of input for this analog
        # array. no need to perform noise modeling
        else:
            finished_stages.append(k)
            ready_input[k] = input_mapping[k]

    # iteratively process the remain analog stages
    while len(finished_stages) != len(analog_sw_stages):
        for sw_stage in analog_sw_stages:
            if sw_stage.name in finished_stages:
                continue

            ready_flag = True
            for in_stage in sw_stage.input_stages:
                if in_stage.name not in finished_stages:
                    ready_flag = False

            # check if all input stages are ready
            if ready_flag:
                analog_array = analog_sw_mapping[sw_stage.name]
                curr_input_list = []
                # include any input that is generated from input stage
                for in_stage in sw_stage.input_stages:
                    for input_data in ready_input[in_stage.name]:
                        curr_input_list.append(input_data)
                # include any input from input mapping file
                for k in input_mapping.keys():
                    if analog_array == analog_sw_mapping[k] and k == sw_stage.name:
                        for input_data in input_mapping[k]:
                            curr_input_list.append(input_data)

                # if the analog array is already computed, we assume for one particular
                # analog stage, one analog array will only be accessed once.
                if analog_array in visited_analog_array:
                    ready_input[sw_stage.name] = curr_input_list
                    finished_stages.append(sw_stage.name)
                # else we will perform functional simulation routine.
                else:
                    # check if the analog array contains the Conv instance and config the convolution instance
                    analog_array._configure_operation(sw_stage = sw_stage)
                    noise_res_list = analog_array.noise(curr_input_list)
                    for pair in noise_res_list:
                        simulation_res[pair[0]] = pair[1]
                    ready_input[sw_stage.name] = noise_res_list[-1][1]
                    finished_stages.append(sw_stage.name)
                    visited_analog_array.append(analog_array)

    # return a dictionaray, key is the software stage name, the value is the simulation result.
    return simulation_res


def _find_analog_interface_stages(sw_stage_list, org_sw_stage_list, org_mapping_dict):
    """
    This function finds those functions that are at the interface between analog and digital
    and creates the input object for digital domain if necessary. 
    If there is analog component, it will create artificial digital input for digital simulation.
    If there is no analog component, it won't create that input since user already created one.

    """
    # if equals, it means that there is no analog component in this pipeline.
    # no need to create digital input.
    if len(sw_stage_list) == len(org_sw_stage_list):
        return sw_stage_list, org_mapping_dict

    # First find which stages are at the interface and their direct output stages.
    init_stages = [] # interface stages
    mapping_dict = {}
    init_output_stages = {} # direct output stages
    for sw_stage in sw_stage_list:
        for in_stage in sw_stage.input_stages:
            if in_stage not in sw_stage_list:
                if in_stage not in init_stages:
                    init_stages.append(in_stage)

                # map interface stages to ADC.
                mapping_dict[in_stage.name] = "ADC"
                # find its direct output stages
                if in_stage not in init_output_stages:
                    init_output_stages[in_stage] = [sw_stage]
                else:
                    init_output_stages[in_stage].append(sw_stage)

    # remove original interface stages from input_stages 
    for sw_stage in sw_stage_list:
        for in_stage in init_stages:
            if in_stage in sw_stage.input_stages:
                sw_stage.input_stages.remove(in_stage)

    for sw_stage in sw_stage_list:
        mapping_dict[sw_stage.name] = org_mapping_dict[sw_stage.name]

    # add back those interface stages using artificial input for digital simulation.
    for sw_stage in init_stages:
        input_data = PixelInput(
            name = sw_stage.name,
            size = sw_stage.output_size
        )

        for output_stage in init_output_stages[sw_stage]:
            output_stage.set_input_stage(input_data)

        sw_stage_list.append(input_data)

    return sw_stage_list, mapping_dict

