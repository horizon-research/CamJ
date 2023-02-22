import os
import sys
# directory
parent_directory = os.path.dirname(os.getcwd())
# setting path
sys.path.append(os.path.dirname(parent_directory))


from camj.sim_core.analog_infra import AnalogArray, AnalogComponent
from camj.sim_core.enum_const import ProcessorLocation, ProcessDomain
from camj.sim_core.analog_utils import check_analog_connect_consistency, compute_total_energy,\
                                  check_analog_pipeline, launch_analog_simulation
from camj.sim_core.pixel_libs import PulseWidthModulationPixel
from camj.sim_core.analog_libs import DigitalToCurrentConverter, CurrentMirror
from camj.sim_core.sw_utils import build_sw_graph

from examples.isscc_22_08v.mapping_file import mapping_function
from examples.isscc_22_08v.sw_pipeline import sw_pipeline

def analog_config():

    analog_arrays = []

    pixel_array = AnalogArray(
        name = "PixelArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(3, 126)],
        num_output = (3, 126)
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
                    pd_supply = 1.8, # [V]
                    ramp_capacitance = 1e-12,  # [F]
                    gate_capacitance = 10e-15,  # [F]
                    num_readout = 1
                ),
                1
            )
        ],
        num_input = [(1, 1)],
        num_output = (1, 1)
    )

    pixel_array.add_component(pixel, (126, 126))

    analog_weight = AnalogArray(
        name = "AnalogWeight",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = None,
        num_output = (3, 3)
    )
    current_dac = AnalogComponent(
        name = "CurrentDAC",
        input_domain = [ProcessDomain.DIGITAL],
        output_domain = ProcessDomain.CURRENT,
        component_list = [
            (
                DigitalToCurrentConverter(
                    # performance parameters
                    supply=1.8,  # [V]
                    load_capacitance=2e-12,  # [F]
                    t_readout=16e-6,  # [s]
                    resolution=4,
                    i_dc=None,  # [A]
                    # noise parameters
                    gain = 1.0,
                    noise = 0.005,
                    enable_prnu = True,
                    prnu_std = 0.001,
                ),
                1
            )
        ],
        num_input = [(1, 1)],
        num_output = (1, 1)
    )
    
    analog_weight.add_component(current_dac, (3, 3))

    pe_array = AnalogArray(
        name = "PEArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(3, 3), (3, 126)],
        num_output = (1, 42)
    )

    pe = AnalogComponent(
        name = "PE",
        input_domain = [ProcessDomain.CURRENT, ProcessDomain.TIME],
        output_domain = ProcessDomain.DIGITAL,
        component_list = [
            (
                CurrentMirror(
                    # performance parameters
                    supply = 1.8,
                    load_capacitance = 2e-12,  # [F]
                    t_readout = 1e-6,  # [s]
                    i_dc = 1e-6,  # [A]
                    # noise parameters
                    gain = 1.0,
                    noise = 0.005,
                    enable_compute = True,
                    enable_prnu = True,
                    prnu_std = 0.001
                ),
                1
            )
        ],
        num_input = [(1, 1)],
        num_output = (1, 1)
    )

    pe_array.add_component(pe, (1, 42))

    pe_array.add_input_array(pixel_array)
    pe_array.add_input_array(analog_weight)

    pixel_array.add_output_array(pe_array)
    analog_weight.add_output_array(pe_array)

    analog_arrays.append(pixel_array)
    analog_arrays.append(analog_weight)
    analog_arrays.append(pe_array)

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
    print("total energy:", total_energy)

