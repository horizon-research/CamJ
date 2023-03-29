import os
import sys

# directory reach
parent_directory = os.path.dirname(os.getcwd())
sys.path.append(os.path.dirname(parent_directory))


# import local modules
from camj.analog.infra import AnalogArray, AnalogComponent
from camj.general.enum import ProcessorLocation, ProcessDomain
from camj.analog.utils import analog_energy_simulation
from camj.analog.component import ActivePixelSensor, ActiveAnalogMemory, ColumnAmplifier, \
                                Comparator, SourceFollower

# import customized config
from examples.ieee_vr22.mapping import mapping_function_w_analog
from examples.ieee_vr22.sw import sw_pipeline_w_analog
from examples.ieee_vr22.customized_analog_component import EventificationUnit


def analog_config():

    full_scale_input_voltage = 1.8 # V
    pixel_full_well_capacity = 10000 # e
    conversion_gain = full_scale_input_voltage / pixel_full_well_capacity
    analog_arrays = []

    pixel_array = AnalogArray(
        name = "PixelArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(2, 640, 1)],
        num_output = (1, 320, 1),
    )
    pixel = AnalogComponent(
        name = "BinningPixel",
        input_domain =[ProcessDomain.OPTICAL],
        output_domain = ProcessDomain.VOLTAGE,
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
                    fd_prnu_std = 0.001,
                    sf_gain = 1.0,
                    sf_prnu_std = 0.001
                ),
                4
            )
        ],
        num_input = [(2, 2, 1)],
        num_output = (1, 1, 1)
    )

    pixel_array.add_component(pixel, (200, 320, 1))

    analog_memory_array = AnalogArray(
        name = "AnalogMemoryArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [],
        num_output = (320, 1, 1),
    )

    analog_memory_unit = AnalogComponent(
        name = "AnalogMemoryunit",
        input_domain = [],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (
                ColumnAmplifier(
                    gain = 1.0,
                    enable_prnu = True,
                    prnu_std = 0.001,
                ), 
                1
            ),
            (
                ActiveAnalogMemory(
                    sample_capacitance = 2e-12,  # [F]
                    comp_capacitance = 2.5e-12,  # [F]
                    t_sample = 1e-6,
                    t_hold = 10e-3,
                    supply = 1.8, # V
                    enable_prnu = True,
                    prnu_std = 0.001,
                ),
                1
            )
        ],
        num_input = [],
        num_output = (1, 1, 1)
    )
    analog_memory_array.add_component(analog_memory_unit, (201, 320, 1))

    eventification_array = AnalogArray(
        name = "EventificationArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(1, 320, 1), (1, 320, 1)],
        num_output = (1, 320, 1),
    )
    eventification_pe = AnalogComponent(
        name = "EventificationPE",
        input_domain = [ProcessDomain.VOLTAGE, ProcessDomain.VOLTAGE],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (
                ActiveAnalogMemory(
                    sample_capacitance = 2e-12,  # [F]
                    comp_capacitance = 2.5e-12,  # [F]
                    t_sample = 1e-6,
                    t_hold = 10e-3,
                    supply = 1.8, # V
                    enable_prnu = True,
                    prnu_std = 0.001,
                ),
                2
            ),
            (
                SourceFollower(
                    supply = 1.8,
                    gain = 1.0,
                    enable_prnu = True,
                    prnu_std = 0.001,
                ),
                2
            ),
            (
                EventificationUnit(
                    event_threshold = 0.3,
                    # performance parameters
                    load_capacitance = 1e-12,  # [F]
                    input_capacitance = 1e-12,  # [F]
                    t_sample = 2e-6,  # [s]
                    t_hold = 10e-3,  # [s]
                    supply = 1.8,  # [V]
                    gain_close = 1,
                    gain_open = 256,
                    differential = False,
                    # noise parameters
                    gain = 1.0,
                    enable_prnu = False,
                    prnu_std = 0.001,
                    enable_offset = False,
                    pixel_offset_voltage = 0.1,
                    col_offset_voltage = 0.05
                ),
                1
            ),
            (
                Comparator(
                    supply = 1.8,
                    enable_prnu = True,
                    prnu_std = 0.001,
                ),
                1
            )

        ],
        num_input = [(1, 1, 1), (1, 1, 1)],
        num_output = (1, 1, 1)
    )
    eventification_array.add_component(eventification_pe, (1, 320, 1))

    pixel_array.add_output_array(eventification_array)
    eventification_array.add_input_array(pixel_array)

    analog_memory_array.add_output_array(eventification_array)
    eventification_array.add_input_array(analog_memory_array)

    analog_arrays.append(pixel_array)
    analog_arrays.append(analog_memory_array)
    analog_arrays.append(eventification_array)

    return analog_arrays

    
if __name__ == '__main__':
    analog_arrays = analog_config()

    sw_stages = sw_pipeline_w_analog()

    mapping_dict = mapping_function_w_analog()

    total_energy = analog_energy_simulation(analog_arrays, sw_stages, mapping_dict)
    print("total energy:", total_energy)

    


