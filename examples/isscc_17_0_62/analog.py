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
from camj.sim_core.analog_libs import PassiveSwitchedCapacitorArray, ColumnAmplifier,\
                                    ActiveAnalogMemory, Comparator
from camj.sim_core.sw_utils import build_sw_graph

from examples.isscc_17_0_62.mapping import mapping_function
from examples.isscc_17_0_62.sw import sw_pipeline

def analog_config():

    analog_arrays = []

    pixel_array = AnalogArray(
        name = "PixelArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(1, 320, 1)],
        num_output = (1, 320, 1)
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
                    dynamic_sf = False,
                    output_vs = 1., # V 
                    num_transistor = 3,
                    enable_cds = False,
                    fd_capacitance = 10e-15,  # [F]
                    load_capacitance = 55.6e-15,  # [F]
                    tech_node = 60,  # [um]
                    pitch = 7,  # [um]
                    array_vsize = 240,
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
    pixel_array.add_component(pixel, (240, 80, 1))

    binning_array = AnalogArray(
        name = "BinningArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(1, 320, 1)],
        num_output = (1, 80, 1)
    )
    col_amp = AnalogComponent(
        name = "ColAmp",
        input_domain =[ProcessDomain.VOLTAGE],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (
                ColumnAmplifier(
                    # performance parameters
                    load_capacitance = 174e-15,  # [F]
                    input_capacitance = 55.6*4e-15,  # [F]
                    t_sample = 1e-6,  # [s]
                    t_frame = 1e-6,  # [s] # TODO: wrong implementation
                    supply = 2.5,  # [V]
                    gain = 4,
                    gain_open = 300,
                    # noise parameters
                    noise = 0.,
                    enable_prnu = False,
                    prnu_std = 0.001,
                    enable_offset = False,
                    pixel_offset_voltage = 0.1,
                    col_offset_voltage = 0.05
                ),
                4
            )
        ],
        num_input = [(1, 4, 1)],
        num_output = (1, 1, 1)
    )
    mem = AnalogComponent(
        name = "Mem",
        input_domain =[ProcessDomain.VOLTAGE],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (
                ActiveAnalogMemory(
                    # performance parameters
                    sample_capacitance = 174e-15,  # [F]
                    comp_capacitance = 55.6e-15,  # [F]
                    t_sample = 1e-3,  # [s]
                    t_hold = 20*2.375e-3,  # [s]
                    supply = 1.2,  # [V]
                    # eqv_reso,# equivalent resolution
                    # opamp_dcgain
                    # noise parameters
                    gain = 1.0,
                    noise = 0.,
                    enable_prnu = False,
                    prnu_std = 0.001,
                ),
                1
            )
        ],
        num_input = [(1, 1, 1)],
        num_output = (1, 1, 1)
    )
    binning_array.add_component(col_amp, (1, 80, 1))
    binning_array.add_component(mem, (20, 80, 1))

    haar_array = AnalogArray(
        name = "HaarArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(20, 80, 1)],
        num_output = (1, 6, 1)
    )
    haar = AnalogComponent(
        name = "Haar",
        input_domain =[ProcessDomain.VOLTAGE],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (
                ColumnAmplifier(
                    # performance parameters
                    load_capacitance = 100e-15,  # [F]
                    input_capacitance = 55.6*2e-15,  # [F]
                    t_sample = 1e-6,  # [s]
                    t_frame = 1e-6,  # [s] # TODO: wrong implementation
                    supply = 2.5,  # [V]
                    gain = 1/64,
                    gain_open = 300,
                    differential = True,
                    # noise parameters
                    noise = 0.,
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
                    # performance parameters
                    supply = 2.5,  # [V]
                    i_bias = 10e-6,  # [A]
                    t_readout = 10e-9,  # [s]
                    # noise parameters
                    gain = 1.0,
                    noise = 0.,
                    enable_prnu = False,
                    prnu_std = 0.001
                ),
                1
            )
        ],
        num_input = [(20, 20, 1)],
        num_output = (1, 1, 1)
    )
    haar_array.add_component(haar, (1, 6, 1))

    analog_arrays.append(pixel_array)
    analog_arrays.append(binning_array)
    analog_arrays.append(haar_array)

    pixel_array.add_output_array(binning_array)
    binning_array.add_input_array(pixel_array)

    binning_array.add_output_array(haar_array)
    haar_array.add_input_array(binning_array)

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

