import os
import sys
# directory reach
parent_directory = os.path.dirname(os.getcwd())
# setting path
sys.path.append(os.path.dirname(parent_directory))

# import local module
from camj.analog.component import ActivePixelSensor, PassiveSwitchedCapacitorArray
from camj.analog.infra import AnalogArray, AnalogComponent
from camj.analog.utils import check_analog_connect_consistency, compute_total_energy,\
                        analog_energy_simulation
from camj.general.enum import ProcessorLocation, ProcessDomain
from camj.sw.utils import build_sw_graph

# import customized module
from examples.isscc_21_back_illuminated.mapping import mapping_function
from examples.isscc_21_back_illuminated.sw import sw_pipeline

def analog_config():

    analog_arrays = []

    pixel_array = AnalogArray(
        name = "PixelArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(1, 1, 1)],
        num_output = (1, 1, 1)
    )
    pixel = AnalogComponent(
        name = "APSPixel",
        input_domain =[ProcessDomain.OPTICAL],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (
                ActivePixelSensor(
                    # performance parameters
                    pd_capacitance = 100e-15, # F
                    pd_supply = 2.5, # V
                    dynamic_sf = True,
                    output_vs = 1.1, # V 
                    num_transistor = 4,
                    enable_cds = True,
                    fd_capacitance = 10e-15,  # [F]
                    load_capacitance = 10e-15,  # [F]
                    tech_node = 110,  # [um]
                    pitch = 4,  # [um]
                    array_vsize = 480,
                    # noise model parameters
                    dark_current_noise = 0.005,
                    enable_dcnu = True,
                    enable_prnu = True,
                    dcnu_std = 0.001,
                    fd_gain = 1.0,
                    fd_prnu_std = 0.001,
                    sf_gain = 1.0,
                    sf_prnu_std = 0.001
                ),
                1
            )
        ],
        num_input = [(1, 1, 1)],
        num_output = (1, 1, 1)
    )

    pixel_array.add_component(pixel, (1520, 2028, 1))

    analog_arrays.append(pixel_array)

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

