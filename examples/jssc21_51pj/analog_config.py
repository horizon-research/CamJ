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
from camj.sim_core.analog_libs import PassiveSwitchedCapacitorArray
from camj.sim_core.sw_utils import build_sw_graph

from examples.jssc21_51pj.mapping_file import mapping_function
from examples.jssc21_51pj.sw_pipeline import sw_pipeline

def analog_config():

    full_scale_input_voltage = 1.8 # V
    pixel_full_well_capacity = 10000 # e
    conversion_gain = full_scale_input_voltage/pixel_full_well_capacity
    analog_arrays = []

    pixel_array = AnalogArray(
        name = "PixelArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(16, 16)],
        num_output = (16, 16)
    )
    pixel = AnalogComponent(
        name = "PWMPixel",
        input_domain =[ProcessDomain.OPTICAL],
        output_domain = ProcessDomain.TIME,
        component_list = [
            (
                ActivePixelSensor(
                    # performance parameters
                    pd_capacitance = 1e-12,
                    pd_supply = 1.8, # V
                    output_vs = 1, #  
                    enable_cds = False,
                    num_transistor = 4,
                    # noise model parameters
                    dark_current_noise = 0.005,
                    enable_dcnu = True,
                    enable_prnu = True,
                    dcnu_std = 0.001,
                    fd_gain = conversion_gain,
                    fd_noise = 0.005,
                    fd_prnu_std = 0.001,
                    sf_gain = 1.0,
                    sf_noise = 0.005,
                    sf_prnu_std = 0.001
                ),
                1
            )
        ],
        num_input = [(1, 1)],
        num_output = (1, 1)
    )

    pixel_array.add_component(pixel, (640, 400))

    cs_array = AnalogArray(
        name = "CSArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(16, 16)],
        num_output = (1, 64)
    )

    cs = AnalogComponent(
        name = "CS",
        input_domain = [ProcessDomain.CURRENT, ProcessDomain.TIME],
        output_domain = ProcessDomain.CURRENT,
        component_list = [
            (
                PassiveSwitchedCapacitorArray(
                    capacitance_array = [1e-12],
                    vs_array = [1],
                ),
                1
            )
        ],
        num_input = [(16, 16)],
        num_output = (1, 64)
    )

    cs_array.add_component(cs, (1, 1))

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

