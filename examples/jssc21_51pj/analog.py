import os
import sys
# directory reach
parent_directory = os.path.dirname(os.getcwd())
# setting path
sys.path.append(os.path.dirname(parent_directory))


from camj.sim_core.analog_infra import AnalogArray, AnalogComponent
from camj.sim_core.enum_const import ProcessorLocation, ProcessDomain
from camj.sim_core.analog_utils import check_analog_connect_consistency, compute_total_energy,\
                                  check_analog_pipeline, launch_analog_simulation
from camj.sim_core.pixel_libs import ActivePixelSensor
from camj.sim_core.analog_libs import Voltage2VoltageConv
from camj.sim_core.sw_utils import build_sw_graph

from examples.jssc21_51pj.mapping import mapping_function
from examples.jssc21_51pj.sw import sw_pipeline

def analog_config():

    analog_arrays = []

    pixel_array = AnalogArray(
        name = "PixelArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(16, 16, 1)],
        num_output = (16, 16, 1)
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
                    load_capacitance = 0,  # [F]
                    tech_node = 110,  # [um]
                    pitch = 4,  # [um]
                    array_vsize = 480,
                    # noise model parameters
                    dark_current_noise = 0.005,
                    enable_dcnu = True,
                    enable_prnu = True,
                    dcnu_std = 0.001,
                    fd_gain = 1.0,
                    fd_noise = 0.005,
                    fd_prnu_std = 0.001,
                    sf_gain = 1.0,
                    sf_noise = 0.005,
                    sf_prnu_std = 0.001
                ),
                1
            )
        ],
        num_input = [(1, 1, 1)],
        num_output = (1, 1, 1)
    )

    pixel_array.add_component(pixel, (480, 640, 1))
    cs_array = AnalogArray(
        name = "CSArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(1, 16, 1)],
        num_output = (1, 4, 1)
    )
    cs = AnalogComponent(
        name = "CS",
        input_domain = [ProcessDomain.VOLTAGE, ProcessDomain.VOLTAGE],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (
                Voltage2VoltageConv(
                    capacitance_array = [
                        1.059e-12, 1.059e-12, 1.059e-12, 1.059e-12, 1.059e-12, 1.059e-12, 1.059e-12, 1.059e-12,
                        1.059e-12, 1.059e-12, 1.059e-12, 1.059e-12, 1.059e-12, 1.059e-12, 1.059e-12, 1.059e-12,
                    ], # F
                    vs_array = [
                        1.1, 1.5, 1.1, 1.5, 1.1, 1.5, 1.1, 1.5,
                        1.1, 1.5, 1.1, 1.5, 1.1, 1.5, 1.1, 1.5, 
                    ], # V
                    sf_load_capacitance = 1e-12,  # [F]
                    sf_supply = 1.8,  # [V]
                    sf_output_vs = 1,  # [V]
                    sf_bias_current = 5e-6,  # [A]
                ),
                2+2 # need to double, because of CDS.
            )
        ],
        num_input = [(1, 16, 1)],
        num_output = (1, 4, 1)
    )
    cs_array.add_component(cs, (1, 1, 1))
    cs_array.add_input_array(pixel_array)

    analog_arrays.append(pixel_array)
    analog_arrays.append(cs_array)

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

    total_energy = launch_analog_simulation(analog_arrays, sw_stage_list, mapping_dict)
    print("total energy:", total_energy)

