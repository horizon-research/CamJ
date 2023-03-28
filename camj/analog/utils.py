import numpy as np
import copy

from camj.analog.infra import AnalogArray, AnalogComponent
from camj.general.enum import ProcessDomain

def _check_component_internal_connect_consistency(analog_component):
    # if this component list contains a single element, if so, directly return
    if len(analog_component.component_list) <= 1:
        return
    # find the head and next component
    head_component = analog_component.component_list[0]
    next_component = analog_component.component_list[1]
    index = 1
    exit_flag = False

    while exit_flag != True:
        # check output domain of the head component is in the input domain of the next component
        # if not, raise an exception
        if not head_component[0].output_domain in next_component[0].input_domain:
            raise Exception("The intra-component connection has mismatch in analog component '%s'" % (analog_component.name))

        head_component = next_component
        if index + 1 < len(analog_component.component_list):
            next_component = analog_component.component_list[index+1]
            index +=1
        else:
            exit_flag = True

def _check_array_internal_connect_consistency(analog_array):
    """Check analog internal connection correctness"""

    # first check the correctness of intra-component connection
    for analog_component in analog_array.components:
        _check_component_internal_connect_consistency(analog_component)

    # if this component list contains a single component, if so, directly return
    if len(analog_array.components) <= 1:
        return

    # check the correctness of inter-component internal connection
    head_component = analog_array.components[0]
    next_component = analog_array.components[1]
    index = 1
    exit_flag = False

    while exit_flag != True:
        # check output domain of the head component is in the input domain of the next component
        # if not, raise an exception
        if head_component.component_list[-1][0].output_domain not in next_component.component_list[0][0].input_domain:
            raise Exception(
                "In '%s', the output domain of '%s' doesn't match the input domain of '%s'." % (
                    analog_array.name, head_component.name, next_component.name
                )
            )

        head_component = next_component
        if index + 1 < len(analog_array.components):
            next_component = analog_array.components[index+1]
            index += 1
        else:
            exit_flag = True


def _find_head_analog_array(analog_arrays):
    """find the header analog array in the analog configuration"""
    head_analog_arrays = []
    for analog_array in analog_arrays:
        if len(analog_array.input_arrays) == 0:
            head_analog_arrays.append(analog_array)

    return head_analog_arrays

def _check_input_output_requirement_consistency(analog_array):
    """check the input-output analog array pair matches

    This function just check if the length of input and output domain list is correct.

    Returns:
        None
    """
    refined_input_domain = []
    for domain in analog_array.input_domain:
        if domain != ProcessDomain.OPTICAL and domain != ProcessDomain.DIGITAL:
            refined_input_domain.append(domain)

    if len(refined_input_domain) != len(analog_array.input_arrays):
        raise Exception("Analog array: '%s' input domain size is not equal to its input_array size" % analog_array.name)


def check_analog_connect_consistency(analog_arrays: list):
    """Check analog connection correctness

    This function checks the correctness of two connected analog components.
    It checks if the output domain of any producer analog component matches
    the input domain of the consumer analog component.

    Args:
        analog_arrays (list): a list of analog arrays.

    Returns:
        None
    """
    # check each analog array internal connection consistency
    for analog_array in analog_arrays:
        _check_array_internal_connect_consistency(analog_array)

    # find those analog stages that don't need any dependencies.
    head_analog_arrays = _find_head_analog_array(analog_arrays)
    new_head_analog_arrays = []
    while len(head_analog_arrays) > 0:
        for analog_array in head_analog_arrays:
            _check_input_output_requirement_consistency(analog_array)
            # this checks if analog input/output domain matchness
            for output_array in analog_array.output_arrays:
                if analog_array.output_domain not in output_array.input_domain:
                    print(analog_array.output_domain, output_array.input_domain)
                    raise Exception(
                        "Analog connection consistency failed. %s's output domain and %s's input domain mismatch." \
                        % (analog_array.name, output_array.name)
                    )

                if output_array not in new_head_analog_arrays:
                    new_head_analog_arrays.append(output_array)

        head_analog_arrays = new_head_analog_arrays
        new_head_analog_arrays = []

def _reverse_sw_to_analog_mapping(analog_arrays, analog_sw_stages, mapping_dict):
    analog_to_sw = {}
    analog_dict = {}

    for analog_array in analog_arrays:
        analog_dict[analog_array.name] = analog_array

    for sw_stage in analog_sw_stages:
        analog_array = analog_dict[mapping_dict[sw_stage.name]]
        if mapping_dict[sw_stage.name] in analog_to_sw:
            analog_to_sw[analog_array].append(sw_stage)
        else:
            analog_to_sw[analog_array] = [sw_stage]

    return analog_to_sw

def _find_analog_output_stages(sw_stages):
    output_stages = []

    # iterate the sw stages that maps to the same analog array,
    # if any sw stage has some output stages that are not part of 
    # the current "sw_stages", then, we consider those sw stages 
    # as output stages.
    for sw_stage in sw_stages:
        for output_stage in sw_stage.output_stages:
            if output_stage not in sw_stages:
                output_stages.append(sw_stage)

    # however, if the output stages is empty after the previous loop,
    # then all the sw stages are independent and they are all output stages
    if len(output_stages) == 0:
        # no need deepcopy, we just need the reference of those sw stages
        # will no modify the output stages
        output_stages = copy.copy(sw_stages)

    return output_stages


def compute_total_energy(analog_arrays, analog_sw_desc, mapping):
    """Compute Energy in Analog Domain

    This function calculates the overall energy consumption of simulated CIS in analog domain.

    Args:
        analog_arrays: a list of analog arrays.
        sw_desc: software pipeline description corresponding to analog domain.
        mapping: software-hardware mapping.

    Returns:
        Energy Result (dict): energy numbers from simulation, stores in a dictionary.
    """
    
    analog_to_sw = _reverse_sw_to_analog_mapping(analog_arrays, analog_sw_desc, mapping)

    ret_dict = {}
    for analog_array in analog_to_sw.keys():
        # check data dependency
        output_stages = _find_analog_output_stages(analog_to_sw[analog_array])
        for output_stage in output_stages:
            sw_size = output_stage.output_size
            hw_size = analog_array.num_output
            cnt = (sw_size[0] * sw_size[1] * sw_size[2]) / (hw_size[0] * hw_size[1] * hw_size[2])
            print(analog_array, analog_to_sw[analog_array][0])
            # check if the analog array contains the Conv instance and config the convolution instance
            # if the analog_to_sw contains multiple sw_stages, we will still use the first sw stage parameters
            # to configure the analog array computation
            analog_array._configure_operation(sw_stage = analog_to_sw[analog_array][0])
            analog_array_energy = analog_array.energy()
            ret_dict[analog_array.name] = int(cnt * analog_array_energy * 1e12) # concert J to pJ
            print("[Energy]", analog_array.name, int(cnt * analog_array_energy * 1e12), "pJ")

    return ret_dict

def _check_analog_pipeline(analog_arrays):

    head_analog_arrays = _find_head_analog_array(analog_arrays)
    finished_analog_arrays = []
    new_head_analog_arrays = []
    idx = 1
    while len(head_analog_arrays) > 0:
        idx += 1
        readiness = True

        # check if this analog array's dependencies are ready
        for analog_array in head_analog_arrays:
            for input_array in analog_array.input_arrays:
                if input_array not in finished_analog_arrays:
                    readiness = False

            if not readiness:
                # add back to next iteration
                new_head_analog_arrays.append(analog_array)
                continue

            finished_analog_arrays.append(analog_array)
            for output_array in analog_array.output_arrays:
                if output_array not in new_head_analog_arrays:
                    new_head_analog_arrays.append(output_array)

        head_analog_arrays = new_head_analog_arrays
        new_head_analog_arrays = []

def _find_analog_sw_stages(sw_stages, analog_arrays, mapping_dict):
    analog_sw_stages = []

    for sw_stage in sw_stages:
        hw_stage_name = mapping_dict[sw_stage.name]

        for analog_array in analog_arrays:
            if analog_array.name == hw_stage_name:
                analog_sw_stages.append(sw_stage)
                break

    return analog_sw_stages

def _find_analog_sw_mapping(sw_stages, analog_arrays, mapping_dict):
    analog_sw_mapping = {}

    for sw_stage in sw_stages:
        hw_stage_name = mapping_dict[sw_stage.name]

        for analog_array in analog_arrays:
            if analog_array.name == hw_stage_name:
                analog_sw_mapping[sw_stage.name] = analog_array
                break

    return analog_sw_mapping

def analog_energy_simulation(analog_arrays, sw_desc, mapping):
    """Launch Energy Simulation in Analog Domain

    The harness function for analog energy simulation.

    Args:
        analog_arrays: a list of analog arrays.
        sw_desc: software pipeline description.
        mapping: software-hardware mapping.

    Returns:
        Energy Result (dict): energy numbers from simulation, stores in a dictionary.

    """

    # check analog connection correctness
    check_analog_connect_consistency(analog_arrays)
    # find stages corresponding to analog computing
    analog_sw_stages = _find_analog_sw_stages(sw_desc, analog_arrays, mapping)
    print("Software stages in analog domain: ", analog_sw_stages)
    # check analog pipeline correctness
    _check_analog_pipeline(analog_arrays)
    # compute analog computing energy
    energy_dict = compute_total_energy(analog_arrays, analog_sw_stages, mapping)
    
    return energy_dict
