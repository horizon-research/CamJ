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

def simple_dummy_config():
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
    return analog_arrays, analog_sw_stages, mapping_dict  


def complex_dummy_config():
    analog_arrays = []

    # define four different analog arrays
    dummy_analog_array1 = AnalogArray(
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
            (DummyAnalogComponent(), 1),
        ]
    )
    dummy_analog_array1.add_component(dummy_analog_comp1, (12, 12, 1))
    
    dummy_analog_array2 = AnalogArray(
        name = "DummyAnalogArr2",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(12, 1)],
        num_output = (12, 1)
    )
    dummy_analog_comp2 = AnalogComponent(
        name = "DummyAnalogComponent2",
        input_domain = [ProcessDomain.OPTICAL],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (DummyAnalogComponent(), 1),
        ]
    )
    dummy_analog_array2.add_component(dummy_analog_comp2, (12, 12, 1))

    dummy_analog_array3 = AnalogArray(
        name = "DummyAnalogArr3",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(12, 1), (12, 1)],
        num_output = (12, 1)
    )
    dummy_analog_comp3 = AnalogComponent(
        name = "DummyAnalogComponent3",
        input_domain = [ProcessDomain.VOLTAGE, ProcessDomain.VOLTAGE],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (DummyAnalogComponent(), 1),
        ],
        num_input = [(1, 1), (1, 1)],
    )
    dummy_analog_array3.add_component(dummy_analog_comp3, (12, 12, 1))

    dummy_analog_array4 = AnalogArray(
        name = "DummyAnalogArr4",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(12, 1)],
        num_output = (12, 1)
    )
    dummy_analog_comp4 = AnalogComponent(
        name = "DummyAnalogComponent4",
        input_domain = [ProcessDomain.VOLTAGE],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (DummyAnalogComponent(), 2),
        ]
    )
    dummy_analog_array4.add_component(dummy_analog_comp4, (12, 1, 1))

    # define the connect
    # arr1  arr2
    #    \  /
    #    arr3
    #      |
    #    arr4
    dummy_analog_array1.add_output_array(dummy_analog_array3)
    dummy_analog_array3.add_input_array(dummy_analog_array1)

    dummy_analog_array2.add_output_array(dummy_analog_array3)
    dummy_analog_array3.add_input_array(dummy_analog_array2)

    dummy_analog_array3.add_output_array(dummy_analog_array4)
    dummy_analog_array4.add_input_array(dummy_analog_array3)

    analog_arrays.append(dummy_analog_array1)
    analog_arrays.append(dummy_analog_array2)
    analog_arrays.append(dummy_analog_array3)
    analog_arrays.append(dummy_analog_array4)

    dummy_op1 = ProcessStage(
        name = "DummyOp1",
        input_size = [(12, 12, 1)],
        kernel_size = [(1, 1, 1)],
        stride = [(1, 1, 1)],
        output_size = (12, 12, 1),
        padding = [Padding.NONE]
    )

    dummy_op2 = ProcessStage(
        name = "DummyOp2",
        input_size = [(12, 12, 1)],
        kernel_size = [(1, 1, 1)],
        stride = [(1, 1, 1)],
        output_size = (12, 12, 1),
        padding = [Padding.NONE]
    )

    dummy_op3 = ProcessStage(
        name = "DummyOp3",
        input_size = [(12, 12, 1), (12, 12, 1)],
        kernel_size = [(1, 1, 1), (1, 1, 1)],
        stride = [(1, 1, 1), (1, 1, 1)],
        output_size = (12, 12, 1),
        padding = [Padding.NONE, Padding.NONE]
    )

    dummy_op4 = ProcessStage(
        name = "DummyOp4",
        input_size = [(12, 12, 1)],
        kernel_size = [(1, 1, 1)],
        stride = [(1, 1, 1)],
        output_size = (12, 12, 1),
        padding = [Padding.NONE]
    )

    # define the software pipeline connections
    dummy_op3.set_input_stage(dummy_op1)
    dummy_op3.set_input_stage(dummy_op2)
    dummy_op4.set_input_stage(dummy_op3)


    # add in the software pipeline
    analog_sw_stages = []
    analog_sw_stages.append(dummy_op1)
    analog_sw_stages.append(dummy_op2)
    analog_sw_stages.append(dummy_op3)
    analog_sw_stages.append(dummy_op4)

    mapping_dict = {
        "DummyOp1": "DummyAnalogArr1",
        "DummyOp2": "DummyAnalogArr2",
        "DummyOp3": "DummyAnalogArr3",
        "DummyOp4": "DummyAnalogArr4",
    }
    return analog_arrays, analog_sw_stages, mapping_dict    

def test_analog_energy_sim():

    analog_arrays, analog_sw_stages, mapping_dict = simple_dummy_config()

    total_energy = compute_total_energy(
        analog_arrays = analog_arrays, 
        analog_sw_stages = analog_sw_stages, 
        mapping_dict = mapping_dict
    )

    assert total_energy == 576, "Total energy number should be 576, but got: %d" % total_energy

def test_analog_noise_sim():

    analog_arrays, analog_sw_stages, mapping_dict = simple_dummy_config()

    hw_dict = {
        "analog" : analog_arrays,
    }

    dummy_input = np.zeros((12, 12, 1))

    input_mapping = {
        "DummyOp" : [dummy_input]
    }

    output = launch_functional_simulation(
        sw_stage_list = analog_sw_stages, 
        hw_dict = hw_dict, 
        mapping_dict = mapping_dict, 
        input_mapping = input_mapping
    )["DummyOp"]

    # there are three dummy analog components in the analog pipeline, so the output 
    # should be all 3.
    assert np.mean(output) == 3, "The average value of output should be 3, got %f" % np.mean(output)

def test_analog_complex_connection():

    analog_arrays, analog_sw_stages, mapping_dict = complex_dummy_config()

    total_energy = compute_total_energy(
        analog_arrays = analog_arrays, 
        analog_sw_stages = analog_sw_stages, 
        mapping_dict = mapping_dict
    )
    assert total_energy == 720, "Total energy number should be 576, but got: %d" % total_energy

    hw_dict = {
        "analog" : analog_arrays,
    }

    dummy_input1 = np.zeros((12, 12, 1))
    dummy_input2 = np.zeros((12, 12, 1))

    input_mapping = {
        "DummyOp1" : [dummy_input1],
        "DummyOp2" : [dummy_input2],

    }

    output = launch_functional_simulation(
        sw_stage_list = analog_sw_stages, 
        hw_dict = hw_dict, 
        mapping_dict = mapping_dict, 
        input_mapping = input_mapping
    )["DummyOp4"]

    # there are three stages, the first stage has two inputs, so overall, the result should be 3.
    assert np.mean(output) == 3, "The average value of output should be 3, got %f" % np.mean(output)

if __name__ == '__main__':
    # test basic energy simulation
    test_analog_energy_sim()
    # test basic noise simulation routine
    test_analog_noise_sim()

    test_analog_complex_connection()



