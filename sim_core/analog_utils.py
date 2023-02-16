import numpy as np
from sim_core.analog_infra import AnalogArray, AnalogComponent
from sim_core.enum_const import ProcessDomain


def check_component_internal_connect_consistency(analog_component):
    # if there is no component or one component inside the analog component,
    # no need to check the consistency
    if len(analog_component.components) <= 1:
        return True

    head_list = analog_component.source_component
    new_head_list = []

    while len(head_list) > 0:
        for component in head_list:
            for output_component in component.output_component:
                if component.output_domain not in output_component.input_domain:
                    raise Exception("Internal connection consistency failed. Domain mismatch.")

                if output_component not in new_head_list:
                    new_head_list.append(output_component)

        print(head_list)
        head_list = new_head_list
        new_head_list = []

def check_array_internal_connect_consistency(analog_array):
    # first check the correctness of every component internal connection
    for analog_component in analog_array.components:
        check_component_internal_connect_consistency(analog_component)

    # then check the correctness of inter-component internal connection
    head_list = analog_array.source_components
    new_head_list = []
    while len(head_list) > 0:
        for component in head_list:
            for output_component in component.output_components:
                if component.output_domain not in output_component.input_domain:
                    raise Exception("Internal connection consistency failed. Domain mismatch.")

                if output_component not in new_head_list:
                    new_head_list.append(output_component)

        head_list = new_head_list
        new_head_list = []

def find_head_analog_array(analog_arrays):
    head_analog_arrays = []
    for analog_array in analog_arrays:
        if len(analog_array.input_arrays) == 0:
            head_analog_arrays.append(analog_array)

    return head_analog_arrays

def check_input_output_requirement_consistency(analog_array):
    refined_input_domain = []
    for domain in analog_array.input_domain:
        if domain != ProcessDomain.OPTICAL and domain != ProcessDomain.DIGITAL:
            refined_input_domain.append(domain)

    if len(refined_input_domain) != len(analog_array.input_arrays):
        raise Exception("Analog array: '%s' input domain size is not equal to its input_array size" % analog_array.name)


def check_analog_connect_consistency(analog_arrays):
    # find those analog stages that don't need any dependencies.
    head_analog_arrays = find_head_analog_array(analog_arrays)
    new_head_analog_arrays = []
    while len(head_analog_arrays) > 0:
        for analog_array in head_analog_arrays:
            check_input_output_requirement_consistency(analog_array)
            for output_array in analog_array.output_arrays:
                if analog_array.output_domain not in output_array.input_domain:
                    raise Exception(
                        "Analog connection consistency failed. %s's output domain and %s's input domain mismatch." \
                        % (analog_array.name, output_array.name)
                    )

                if output_array not in new_head_analog_arrays:
                    new_head_analog_arrays.append(output_array)

        head_analog_arrays = new_head_analog_arrays
        new_head_analog_arrays = []

def reverse_sw_to_analog_mapping(analog_arrays, analog_sw_stages, mapping_dict):
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

def find_analog_output_stages(sw_stages):
    output_stages = []

    for sw_stage in sw_stages:
        for output_stage in sw_stage.output_stages:
            if output_stage not in sw_stages:
                output_stages.append(sw_stage)

    return output_stages


def compute_total_energy(analog_arrays, analog_sw_stages, mapping_dict):
    
    analog_to_sw = reverse_sw_to_analog_mapping(analog_arrays, analog_sw_stages, mapping_dict)

    total_energy = 0
    for analog_array in analog_to_sw.keys():
        # check data dependency
        output_stages = find_analog_output_stages(analog_to_sw[analog_array])
        for output_stage in output_stages:
            sw_size = output_stage.output_size
            hw_size = analog_array.num_output
            cnt = (sw_size[0] * sw_size[1] * sw_size[2]) / (hw_size[0] * hw_size[1])
            total_energy += cnt * analog_array.energy()

    return total_energy

def check_analog_pipeline(analog_arrays):

    head_analog_arrays = find_head_analog_array(analog_arrays)
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

def find_analog_sw_stages(sw_stages, analog_arrays, mapping_dict):
    analog_sw_stages = []

    for sw_stage in sw_stages:
        hw_stage_name = mapping_dict[sw_stage.name]

        for analog_array in analog_arrays:
            if analog_array.name == hw_stage_name:
                analog_sw_stages.append(sw_stage)
                break

    return analog_sw_stages

def find_analog_sw_mapping(sw_stages, analog_arrays, mapping_dict):
    analog_sw_mapping = {}

    for sw_stage in sw_stages:
        hw_stage_name = mapping_dict[sw_stage.name]

        for analog_array in analog_arrays:
            if analog_array.name == hw_stage_name:
                analog_sw_mapping[sw_stage.name] = analog_array
                break

    return analog_sw_mapping

def launch_analog_simulation(analog_arrays, sw_stages, mapping_dict):
    # check analog connection correctness
    check_analog_connect_consistency(analog_arrays)
    # find stages corresponding to analog computing
    analog_sw_stages = find_analog_sw_stages(sw_stages, analog_arrays, mapping_dict)
    # check analog pipeline correctness
    check_analog_pipeline(analog_arrays)
    # compute analog computing energy
    total_energy = compute_total_energy(analog_arrays, analog_sw_stages, mapping_dict)
    
    return total_energy


def gm_id(
        load_capacitance,
        gain,
        bandwidth,
        differential=True,
        inversion_level='moderate'
    ):
    if inversion_level == 'strong':
        gm_id_ratio = 10
    elif inversion_level == 'moderate':
        gm_id_ratio = 15
    elif inversion_level == 'weak':
        gm_id_ratio = 20
    num_branch = np.where(differential, 2, 1)
    gm = 2 * np.pi * load_capacitance * gain * bandwidth
    id = gm / gm_id_ratio * num_branch * 1e9  # [nA]

    return [id, gm]


def get_pixel_parasitic(
        array_v,
        tech_node,  # [nm]
        pitch  # [um]
    ):
    C_p = 9e-15 / 130 / 5 * tech_node * pitch * array_v
    return C_p


def get_nominal_supply(tech_node):
    if 130 < tech_node <= 180:
        supply = 1.8
    if 65 < tech_node <= 130:
        supply = 1.5
    if tech_node <= 65:
        supply = 1.1
    else:
        raise Exception("Defined tech_node is not supported.")
    return supply


def parallel_impedance(impedance_array):
    impedance = np.reciprocal(np.sum(np.reciprocal(impedance_array)))
    return impedance


def get_delay(
        current_stage_output_impedance,
        next_stage_input_impedance,
        current_stage_output_capacitance,
        next_stage_input_capacitance
    ):
    # 5*Tau represents charging to 99% of the full voltage from 0
    delay = 5 * (parallel_impedance([current_stage_output_impedance, next_stage_input_impedance])) * \
            (current_stage_output_capacitance + next_stage_input_capacitance)
    return delay