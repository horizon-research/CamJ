import os
import sys
# directory
parent_directory = os.path.dirname(os.getcwd())
# setting path
sys.path.append(os.path.dirname(parent_directory))


from camj.sim_core.analog_infra import AnalogArray, AnalogComponent
from camj.sim_core.enum_const import ProcessorLocation, ProcessDomain
from camj.sim_core.analog_utils import check_analog_connect_consistency, compute_total_energy,\
                                       launch_analog_simulation
from camj.sim_core.pixel_libs import PulseWidthModulationPixel
from camj.sim_core.analog_libs import DigitalToCurrentConverter, CurrentMirror, Comparator,\
                                      PassiveAnalogMemory, Time2CurrentConv
from camj.sim_core.sw_utils import build_sw_graph

from examples.isscc_22_08v.mapping import mapping_function
from examples.isscc_22_08v.sw import sw_pipeline

def analog_config():

    analog_arrays = []

    pixel_array = AnalogArray(
        name = "PixelArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(3, 126, 1)],
        num_output = (3, 126, 1)
    )
    pixel = AnalogComponent(
        name = "PWMPixel",
        input_domain =[ProcessDomain.OPTICAL],
        output_domain = ProcessDomain.TIME,
        component_list = [
            (
                PulseWidthModulationPixel(
                    # performance parameters
                    pd_capacitance = 100e-15, # [F]
                    pd_supply = 0.8, # [V]
                    array_vsize = 126, # pixel array vertical size
                    ramp_capacitance = 1e-12,  # [F]
                    gate_capacitance = 10e-15,  # [F]
                    num_readout = 8
                ),
                1
            )
        ],
        num_input = [(1, 1, 1)],
        num_output = (1, 1, 1)
    )
    pixel_array.add_component(pixel, (126, 126, 1))

    analog_weight = AnalogArray(
        name = "AnalogWeight",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = None,
        num_output = (3, 3, 3)
    )
    current_dac = AnalogComponent(
        name = "CurrentDAC",
        input_domain = [ProcessDomain.DIGITAL],
        output_domain = ProcessDomain.CURRENT,
        component_list = [
            (
                DigitalToCurrentConverter(
                    # performance parameters
                    supply = 0.8,  # [V]
                    load_capacitance = 2e-12,  # [F]
                    t_readout = 7.9e-6,  # [s]
                    resolution = 4,
                    i_dc = None,  # [A]
                    # noise parameters
                    gain = 1.0,
                    noise = 0.005,
                    enable_prnu = True,
                    prnu_std = 0.001,
                ),
                1
            )
        ],
        num_input = [(1, 1, 1)],
        num_output = (1, 1, 1)
    )
    analog_weight.add_component(current_dac, (3, 3, 3))

    conv_array = AnalogArray(
        name = "ConvArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(3, 3, 1), (3, 126, 1)],
        num_output = (1, 42, 1)
    )

    conv = AnalogComponent(
        name = "Conv",
        input_domain = [ProcessDomain.CURRENT, ProcessDomain.TIME],
        output_domain = ProcessDomain.CURRENT,
        component_list = [
            (
                Time2CurrentConv(
                    cm_supply = 0.8,
                    cm_load_capacitance = 2e-12,  # [F]
                    cm_t_readout = 7.9e-6,  # [s]
                    cm_i_dc = None,  # [A]
                    # performance parameters for analog memory
                    am_capacitance = 2e-12,  # [F]
                    am_supply = 0.8,  # [V]
                    # eqv_reso  # equivalent resolution
                    # noise parameters for current mirror
                    cm_gain = 1.0,
                    cm_noise = 0.,
                    cm_enable_prnu = False,
                    cm_prnu_std = 0.001,
                    # noise parameters for analog memory
                    am_gain = 1.0,
                    am_noise = 0.,
                    am_enable_prnu = False,
                    am_prnu_std = 0.001,
                ),
                1
            ),
            (
                PassiveAnalogMemory(
                    # performance parameters
                    capacitance = 1e-12,  # [F]
                    supply = 0.8,  # [V]
                    # eqv_reso  # equivalent resolution
                    # noise parameters
                    gain = 1.0,
                    noise = 0.,
                    enable_prnu = False,
                    prnu_std = 0.001,
                ), 
                2
            ),
        ],
        num_input = [(3, 3, 3), (3, 3, 3)],
        num_output = (1, 1, 1)
    )
    conv_array.add_component(conv, (1, 42, 1))

    relu_array = AnalogArray(
        name = "ReLUArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(1, 42, 1)],
        num_output = (1, 42, 1)
    )
    relu = AnalogComponent(
        name = "ReLU",
        input_domain = [ProcessDomain.CURRENT],
        output_domain = ProcessDomain.DIGITAL,
        component_list = [
            (
                Comparator(
                    # performance parameters
                    supply = 0.8,  # [V]
                    i_bias = 10e-6,  # [A]
                    t_readout = 1e-9,  # [s]
                    # noise parameters
                    gain = 1.0,
                    noise = 0.005,
                    enable_prnu = True,
                    prnu_std = 0.001
                ),
                1
            )
        ],
        num_input = [(1, 1, 1)],
        num_output = (1, 1, 1)
    )

    relu_array.add_component(relu, (1, 42, 1))

    pixel_array.add_output_array(conv_array)
    conv_array.add_input_array(pixel_array)

    analog_weight.add_output_array(conv_array)
    conv_array.add_input_array(analog_weight)

    conv_array.add_output_array(relu_array)
    relu_array.add_input_array(conv_array)

    analog_arrays.append(pixel_array)
    analog_arrays.append(analog_weight)
    analog_arrays.append(conv_array)
    analog_arrays.append(relu_array)

    return analog_arrays

if __name__ == '__main__':
    # get the configs
    analog_arrays = analog_config()
    mapping_dict = mapping_function()
    sw_stage_list = sw_pipeline()
    # build sw stage connections
    build_sw_graph(sw_stage_list)

    check_analog_connect_consistency(analog_arrays)
    # analog energy simulation
    total_energy = launch_analog_simulation(analog_arrays, sw_stage_list, mapping_dict)
    print("total energy:", total_energy, "pJ")

