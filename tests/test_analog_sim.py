import os
import sys
# directory reach
directory = os.getcwd()
parent_directory = os.path.dirname(directory)
# setting path
sys.path.append(os.path.dirname(directory))
sys.path.append(os.path.dirname(parent_directory))

import numpy as np 

from sim_core.analog_infra import AnalogComponent, AnalogArray
from sim_core.analog_utils import launch_analog_simulation, compute_total_energy
from sim_core.sw_interface import ProcessStage
from sim_core.enum_const import ProcessorLocation, ProcessDomain, Padding
from functional_core.launch import launch_functional_simulation


class DummyAnalogComponent(object):
    """docstring for DummyAnalogComponent"""
    def __init__(self):
        self.name = "Dummy"

    def energy(self):
        return 1

    def noise(self, input_signal_list):
        output_signal_list = []

        for input_signal in input_signal_list:
            output_signal_list.append(
                input_signal + 1
            )

        return output_signal_list


def test_analog_energy_sim():
    analog_arrays = []

    dummy_analog_array = AnalogArray(
        name = "DummyAnalogArr1",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(12, 1)],
        num_output = (12, 1)
    )

    dummy_analog_comp1 = AnalogComponent(
        name = "DummyAnalogComponent1",
        input_domain = [ProcessDomain.OPTICAL],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (
                DummyAnalogComponent(),
                2
            ),
            (
                DummyAnalogComponent(),
                1
            )
        ]
    )

    dummy_analog_array.add_component(dummy_analog_comp1, (12, 12, 1))

    dummy_analog_comp2 = AnalogComponent(
        name = "DummyAnalogComponent2",
        input_domain = [ProcessDomain.VOLTAGE],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (
                DummyAnalogComponent(),
                1
            ),
        ]
    )

    dummy_analog_array.add_component(dummy_analog_comp2, (12, 1, 1))

    analog_arrays.append(dummy_analog_array)

    analog_sw_stages = [
        ProcessStage(
            name = "DummyOp",
            input_size = [(12, 12, 1)],
            kernel_size = [(1, 1, 1)],
            stride = [(1, 1, 1)],
            output_size = (12, 12, 1),
            padding = [Padding.NONE]
        )
    ]

    mapping_dict = {
        "DummyOp": "DummyAnalogArr1"
    }

    total_energy = compute_total_energy(
        analog_arrays = analog_arrays, 
        analog_sw_stages = analog_sw_stages, 
        mapping_dict = mapping_dict
    )

    assert total_energy == 576, "Total energy number should be 576, but got: %d" % total_energy

def test_analog_noise_sim():
    analog_arrays = []

    dummy_analog_array = AnalogArray(
        name = "DummyAnalogArr1",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(12, 1)],
        num_output = (12, 1)
    )

    dummy_analog_comp1 = AnalogComponent(
        name = "DummyAnalogComponent1",
        input_domain = [ProcessDomain.OPTICAL],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (
                DummyAnalogComponent(),
                2
            ),
            (
                DummyAnalogComponent(),
                1
            )
        ]
    )

    dummy_analog_array.add_component(dummy_analog_comp1, (12, 12, 1))

    dummy_analog_comp2 = AnalogComponent(
        name = "DummyAnalogComponent2",
        input_domain = [ProcessDomain.VOLTAGE],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (
                DummyAnalogComponent(),
                1
            ),
        ]
    )

    dummy_analog_array.add_component(dummy_analog_comp2, (12, 1, 1))

    analog_arrays.append(dummy_analog_array)

    analog_sw_stages = [
        ProcessStage(
            name = "DummyOp",
            input_size = [(12, 12, 1)],
            kernel_size = [(1, 1, 1)],
            stride = [(1, 1, 1)],
            output_size = (12, 12, 1),
            padding = [Padding.NONE]
        )
    ]

    mapping_dict = {
        "DummyOp": "DummyAnalogArr1"
    }

    total_energy = compute_total_energy(
        analog_arrays = analog_arrays, 
        analog_sw_stages = analog_sw_stages, 
        mapping_dict = mapping_dict
    )

    assert total_energy == 576, "Total energy number should be 576, but got: %d" % total_energy


if __name__ == '__main__':
    
    test_analog_energy_sim()

