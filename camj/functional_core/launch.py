import copy
import numpy as np
from inspect import signature

from camj.sim_core.sw_utils import build_sw_graph
from camj.sim_core.analog_utils import find_analog_sw_stages, find_analog_sw_mapping
                    
def process_signal_stage(stage, input_signals):

    output_signals = []
    sig = signature(stage.apply_gain_and_noise)
    
    if len(sig.parameters) == 1:
        for input_signal in input_signals:
            output_signal = stage.apply_gain_and_noise(input_signal)
            if isinstance(output_signal, tuple):
                for item in output_signal:
                    output_signals.append(item)
            else:
                output_signals.append(output_signal)
    elif len(sig.parameters) == 2:
        if len(input_signals) != 2:
            raise Exception("Input for this stage needs to be 2!")
        output_signal = stage.apply_gain_and_noise(input_signals[0], input_signals[1])
        if isinstance(output_signal, tuple):
                for item in output_signal:
                    output_signals.append(item)
        else:
            output_signals.append(output_signal)
    else:
        raise Exception("Incompatible input and processing stage pair!")

    return output_signals

def default_functional_simulation(functional_pipeline_list, input_list):

    curr_input = input_list
    curr_output = []

    for stage in functional_pipeline_list:
        if isinstance(stage, tuple) or isinstance(stage, list):
            for s in stage:
                output_signals = process_signal_stage(s, curr_input)
                for output_signal in output_signals:
                    curr_output.append(output_signal)
        else:
            output_signals = process_signal_stage(stage, curr_input)
            for output_signal in output_signals:
                curr_output.append(output_signal)

        curr_input = curr_output
        curr_output = []

    return curr_input

def launch_functional_simulation(sw_desc, hw_desc, mapping, input_mapping):
    # deep copy in case the function modify the orginal data
    hw_dict = copy.deepcopy(hw_desc)
    mapping_dict = copy.deepcopy(mapping)
    sw_stage_list = copy.deepcopy(sw_desc)
    # complete the software stages data dependency graph.
    build_sw_graph(sw_stage_list)

    # find software stages that are computed in analog domain
    analog_sw_stages = find_analog_sw_stages(sw_stage_list, hw_dict["analog"], mapping_dict)
    analog_sw_mapping = find_analog_sw_mapping(sw_stage_list, hw_dict["analog"], mapping_dict)

    finished_stages = []
    ready_input = {}
    visited_analog_array = []
    simulation_res = {}
    # first process those analog stages that are initial stage in analog pipeline.
    for k in input_mapping.keys():
        analog_array = analog_sw_mapping[k]
        # check if the analog array contains the Conv instance and config the convolution instance
        analog_array.configure_operation(sw_stage = k)
        noise_res_list = analog_array.noise(input_mapping[k])
        for pair in noise_res_list:
            simulation_res[pair[0]] = pair[1]
        ready_input[k] = noise_res_list[-1][1]
        finished_stages.append(k)
        visited_analog_array.append(analog_array)

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
                for in_stage in sw_stage.input_stages:
                    for input_data in ready_input[in_stage.name]:
                        curr_input_list.append(input_data)

                # if the analog array is already computed, we assume for one particular
                # analog stage, one analog array will only be accessed once.
                if analog_array in visited_analog_array:
                    ready_input[sw_stage.name] = curr_input_list
                    finished_stages.append(sw_stage.name)
                # else we will perform functional simulation routine.
                else:
                    # check if the analog array contains the Conv instance and config the convolution instance
                    analog_array.configure_operation(sw_stage = sw_stage)
                    noise_res_list = analog_array.noise(curr_input_list)
                    for pair in noise_res_list:
                        simulation_res[pair[0]] = pair[1]
                    ready_input[sw_stage.name] = noise_res_list[-1][1]
                    finished_stages.append(sw_stage.name)
                    visited_analog_array.append(analog_array)

    # return a dictionaray, key is the software stage name, the value is the simulation result.
    return simulation_res




