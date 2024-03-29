import os
import sys
# directory
parent_directory = os.path.dirname(os.getcwd())
# setting path
sys.path.append(os.path.dirname(parent_directory))

# import local modules
from camj.analog.component import ActivePixelSensor, Comparator, PassiveAnalogMemory
from camj.analog.infra import AnalogArray, AnalogComponent
from camj.analog.utils import check_analog_connect_consistency, compute_total_energy,\
                            analog_energy_simulation
from camj.general.enum import ProcessorLocation, ProcessDomain
from camj.sw.utils import build_sw_graph

# import customized modules
from examples.tcas_i22.mapping import mapping_function
from examples.tcas_i22.sw import sw_pipeline

def analog_config():

    analog_arrays = []

    pixel_array = AnalogArray(
        name = "PixelArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(32, 32, 1)],
        num_output = (1, 1, 1)
    )
    pixel = AnalogComponent(
        name = "APS+PE",
        input_domain =[ProcessDomain.OPTICAL],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (
                PassiveAnalogMemory(
                    # performance parameters
                    sample_capacitance = 100e-12,  # [F]
                    supply = 1.8,  # [V]
                    # eqv_reso  # equivalent resolution
                    # noise parameters
                    enable_prnu = False,
                    prnu_std = 0.001,
                ), 
                1
            ),

        ],
        num_input = [(32, 32, 1)],
        num_output = (1, 1, 1)
    )
    pixel_array.add_component(pixel, (1, 1, 1))

    analog_arrays.append(pixel_array)

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
    total_energy = analog_energy_simulation(analog_arrays, sw_stage_list, mapping_dict)
    print("total energy:", total_energy)

