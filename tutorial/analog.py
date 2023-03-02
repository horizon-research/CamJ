import os
import sys
# setting path
sys.path.append(os.path.dirname(os.getcwd()))


from camj.sim_core.analog_infra import AnalogArray, AnalogComponent
from camj.sim_core.enum_const import ProcessorLocation, ProcessDomain
from camj.sim_core.analog_utils import launch_analog_simulation
from camj.sim_core.pixel_libs import ActivePixelSensor
from camj.sim_core.analog_libs import ColumnAmplifier

from tutorial.mapping import mapping_function
from tutorial.sw import sw_pipeline


def analog_config():

    full_scale_input_voltage = 1.8 # V
    pixel_full_well_capacity = 10000 # e
    conversion_gain = full_scale_input_voltage / pixel_full_well_capacity
    analog_arrays = []

    pixel_array = AnalogArray(
        name = "PixelArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(1, 36, 1)],   # H, W, C
        num_output = (1, 36, 1),    # H, W, C
    )
    pixel = AnalogComponent(
        name = "Pixel",
        input_domain =[ProcessDomain.OPTICAL],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (
                ActivePixelSensor(
                    # performance parameters
                    pd_capacitance = 100e-15, # F
                    pd_supply = 1.8, # V
                    dynamic_sf = True,
                    output_vs = 1.1, # V 
                    num_transistor = 3,
                    enable_cds = False,
                    fd_capacitance = 10e-15,  # [F]
                    load_capacitance = 0,  # [F]
                    tech_node = 110,  # [um]
                    pitch = 4,  # [um]
                    array_vsize = 480,
                    # noise model parameters
                    dark_current_noise = 0.05,
                    enable_dcnu = True,
                    enable_prnu = True,
                    dcnu_std = 0.01,
                    fd_gain = conversion_gain,
                    fd_noise = 0.05,
                    fd_prnu_std = 0.01,
                    sf_gain = 1.0,
                    sf_noise = 0.05,
                    sf_prnu_std = 0.01
                ),
                1
            )
        ],
        num_input = [(1, 1, 1)],
        num_output = (1, 1, 1)
    )
    pixel_array.add_component(pixel, (36, 36, 1))   # H, W, C
    
    col_amp = AnalogComponent(
        name = "ColumnAmplifier",
        input_domain =[ProcessDomain.VOLTAGE],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (
                ColumnAmplifier(
                    load_capacitance = 1e-23,  # [F]
                    input_capacitance = 1e-15,  # [F]
                    t_sample = 2e-6,  # [s]
                    t_frame = 10e-3,  # [s]
                    supply = 1.8,  # [V]
                    gain = 1,
                    # noise parameters
                    noise = 0.05,
                    enable_prnu = True,
                    prnu_std = 0.01,
                ),
                1
            )
        ],
        num_input = [(1, 1, 1)],
        num_output = (1, 1, 1)
    )
    pixel_array.add_component(col_amp, (1, 36, 1))  # H, W, C

    analog_arrays.append(pixel_array)

    return analog_arrays

    
if __name__ == '__main__':
    
    analog_arrays = analog_config()
    sw_stages = sw_pipeline()
    mapping_dict = mapping_function()

    total_energy = launch_analog_simulation(analog_arrays, sw_stages, mapping_dict)

    print("total energy:", total_energy)

    


