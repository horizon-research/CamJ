import os
import sys
# directory reach
parent_directory = os.path.dirname(os.getcwd())
# setting path
sys.path.append(os.path.dirname(parent_directory))

# import local modules
from camj.analog.component import ActivePixelSensor, GeneralCircuit, Voltage2VoltageConv,\
                                ColumnAmplifier, Comparator, PassiveSwitchedCapacitorArray
from camj.analog.infra import AnalogArray, AnalogComponent
from camj.analog.utils import check_analog_connect_consistency, compute_total_energy,\
                            analog_energy_simulation
from camj.general.enum import ProcessorLocation, ProcessDomain
from camj.sw.utils import build_sw_graph

# import customized modules
from examples.jssc_19.mapping import mapping_function
from examples.jssc_19.sw import sw_pipeline

def analog_config():

    analog_arrays = []

    pixel_array = AnalogArray(
        name = "PixelArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(1, 240, 1)],
        num_output = (1, 240, 1)
    )
    pixel = AnalogComponent(
        name = "4T-APS",
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
                    num_transistor = 4,
                    enable_cds = True,
                    fd_capacitance = 10e-15,  # [F]
                    load_capacitance = 100e-15,  # [F]
                    tech_node = 130,  # [nm]
                    pitch = 5,  # [um]
                    array_vsize = 320,
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
            ),
            (
                GeneralCircuit(
                    supply = 1.5,  # [V]
                    t_operation = 15e-6,  # [s]
                    i_dc = 1.1e-6,  # [s]
                ),
                1
            ),
            (
                PassiveSwitchedCapacitorArray(
                    # peformance parameters
                    capacitance_array = [100e-15, 100e-15],
                    vs_array = [1.5, 1.5],
                ),
                1
            )

        ],
        num_input = [(1, 1, 1)],
        num_output = (1, 1, 1)
    )

    pixel_array.add_component(pixel, (320, 240, 1))

    pe_array = AnalogArray(
        name = "PEArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(1, 240, 1)],
        num_output = (1, 240, 1)
    )

    pe = AnalogComponent(
        name = "PE",
        input_domain = [ProcessDomain.VOLTAGE],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (
                Voltage2VoltageConv(
                    # peformance parameters
                    capacitance_array = [119e-15, 119e-15, 2.2*119e-15, 0.54*119e-15, 0, 0, 0, 0, 0],
                    vs_array = [0.55, 0.55, 0.55, 0.55, 0, 0, 0, 0, 0],
                    sf_load_capacitance = 1e-12,  # [F]
                    sf_supply = 1.8,  # [V]
                    sf_output_vs = 1,  # [V]
                    sf_bias_current = 5e-6,  # [A]
                    # noise parameters
                    sf_enable_prnu = False,
                    sf_prnu_std = 0.001,
                ),
                2
            ),
            (
                ColumnAmplifier(
                    # performance parameters
                    load_capacitance = 100e-15,  # [F]
                    input_capacitance = 0,  # [F]
                    t_sample = 1e-7,  # [s]
                    t_hold = 2.3e-6,  # [s]
                    supply = 2.5,  # [V]
                    gain_close = 1,
                    gain_open = 6,
                    differential = True,
                    # noise parameters
                    gain = 1,
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
                    enable_prnu = False,
                    prnu_std = 0.001
                ),
                1
            )
        ],
        num_input = [(1, 1, 1)],
        num_output = (1, 1, 1)
    )

    pe_array.add_component(pe, (1, 240, 1))

    pe_array.add_input_array(pixel_array)
    pixel_array.add_output_array(pe_array)

    analog_arrays.append(pixel_array)
    analog_arrays.append(pe_array)

    return analog_arrays

    
if __name__ == '__main__':
    # get the configuration files
    analog_arrays = analog_config()
    mapping_dict = mapping_function()
    sw_stage_list = sw_pipeline()
    # build sw stage connection
    build_sw_graph(sw_stage_list)

    total_energy = analog_energy_simulation(analog_arrays, sw_stage_list, mapping_dict)
    print("total energy:", total_energy)

