import numpy as np
from analog_infra import AnalogArray, AnalogComponent


def check_unit_internal_connect_consistency(analog_unit):
    # if there is no component or one component inside the analog unit,
    # no need to check the consistency
    if len(analog_unit.components) <= 1:
        return True

    head_list = analog_unit.source_component
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
    # first check the correctness of every unit internal connection
    for analog_unit in analog_array.units:
        check_unit_internal_connect_consistency(analog_unit)

    # then check the correctness of inter-unit internal connection
    head_list = analog_array.source_units
    new_head_list = []
    while len(head_list) > 0:
        for unit in head_list:
            for output_unit in unit.output_units:
                if unit.output_domain not in output_unit.input_domain:
                    raise Exception("Internal connection consistency failed. Domain mismatch.")

                if output_unit not in new_head_list:
                    new_head_list.append(output_unit)

        head_list = new_head_list
        new_head_list = []


def find_head_analog_array(analog_arrays):
    head_analog_arrays = []
    for analog_array in analog_arrays:
        if len(analog_array.source_units) == 0:
            head_analog_arrays.append(analog_array)

    return head_analog_arrays


def check_analog_connect_consistency(analog_arrays):
    for analog_array in analog_arrays:
        check_array_internal_connect_consistency(analog_array)

    head_analog_arrays = find_head_analog_array(analog_arrays)
    new_head_analog_arrays = []
    while len(head_analog_arrays) > 0:
        for analog_array in head_analog_arrays:
            for output_array in analog_array.output_arrays:
                print(analog_array.name, output_array.name)
                if analog_array.output_domain not in output_array.input_domain:
                    raise Exception("Internal connection consistency failed. Domain mismatch.")

                if output_array not in new_head_analog_arrays:
                    new_head_analog_arrays.append(output_array)

        head_analog_arrays = new_head_analog_arrays
        new_head_analog_arrays = []


def compute_total_energy(analog_arrays):
    total_energy = 0

    for analog_array in analog_arrays:
        total_energy += analog_array.energy()

    return total_energy
