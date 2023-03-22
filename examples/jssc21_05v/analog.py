import os
import sys
# directory reach
parent_directory = os.path.dirname(os.getcwd())
# setting path
sys.path.append(os.path.dirname(parent_directory))

# import local module
from camj.analog.component import PulseWidthModulationPixel, DigitalToCurrentConverter,\
                            Time2VoltageConv
from camj.analog.infra import AnalogArray, AnalogComponent
from camj.analog.utils import check_analog_connect_consistency, compute_total_energy,\
                            analog_energy_simulation
from camj.general.enum import ProcessorLocation, ProcessDomain
from camj.sw.utils import build_sw_graph

# import customized module
from examples.jssc21_05v.mapping import mapping_function
from examples.jssc21_05v.sw import sw_pipeline

def analog_config():

    analog_arrays = []

    pixel_array = AnalogArray(
        name = "PixelArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(3, 128, 1)],
        num_output = (3, 128, 1)
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
                    pd_supply = 0.5, # [V]
                    array_vsize = 128, # pixel array vertical size
                    ramp_capacitance = 1e-12,  # [F]
                    gate_capacitance = 10e-15,  # [F]
                    num_readout = 9
                ),
                1
            )
        ],
        num_input = [(1, 1, 1)],
        num_output = (1, 1, 1)
    )

    pixel_array.add_component(pixel, (128, 128, 1))

    analog_weight = AnalogArray(
        name = "AnalogWeight",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = None,
        num_output = (3, 3, 1)
    )
    current_dac = AnalogComponent(
        name = "CurrentDAC",
        input_domain = [ProcessDomain.DIGITAL],
        output_domain = ProcessDomain.CURRENT,
        component_list = [
            (
                DigitalToCurrentConverter(
                    # performance parameters
                    supply = 0.5,  # [V]
                    load_capacitance = 2e-12,  # [F]
                    t_readout = 16e-6,  # [s]
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
    
    analog_weight.add_component(current_dac, (3, 3, 1))

    pe_array = AnalogArray(
        name = "PEArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(3, 3, 1), (3, 128, 1)],
        num_output = (1, 128, 1)
    )

    pe = AnalogComponent(
        name = "PE",
        input_domain = [ProcessDomain.CURRENT, ProcessDomain.TIME],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (
                Time2VoltageConv(
                    cm_supply = 0.5,
                    cm_load_capacitance = 2e-12,  # [F]
                    cm_t_readout = 16e-6,  # [s]
                    cm_i_dc = None,  # [A]
                    # performance parameters for analog memory
                    am_sample_capacitance = 2e-12,  # [F]
                    am_supply = 0.5,  # [V]
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
            )
        ],
        num_input = [(3, 1, 1), (3, 1, 1)],
        num_output = (1, 1, 1)
    )

    pe_array.add_component(pe, (1, 128, 1))

    pe_array.add_input_array(pixel_array)
    pe_array.add_input_array(analog_weight)

    pixel_array.add_output_array(pe_array)
    analog_weight.add_output_array(pe_array)

    analog_arrays.append(pixel_array)
    analog_arrays.append(analog_weight)
    analog_arrays.append(pe_array)

    return analog_arrays

    
if __name__ == '__main__':
    # get the configuration files
    analog_arrays = analog_config()
    mapping_dict = mapping_function()
    sw_stage_list = sw_pipeline()
    # build sw stage connection
    build_sw_graph(sw_stage_list)
    # check connection consistency
    check_analog_connect_consistency(analog_arrays)

    total_energy = analog_energy_simulation(analog_arrays, sw_stage_list, mapping_dict)
    print("total energy:", total_energy)

