import os
import sys
# directory
parent_directory = os.path.dirname(os.getcwd())
# setting path
sys.path.append(os.path.dirname(parent_directory))


from camj.sim_core.analog_infra import AnalogArray, AnalogComponent
from camj.sim_core.enum_const import ProcessorLocation, ProcessDomain
from camj.sim_core.analog_utils import check_analog_connect_consistency, compute_total_energy,\
                                       launch_analog_simulation
from camj.sim_core.pixel_libs import ActivePixelSensor
from camj.sim_core.analog_libs import PassiveSwitchedCapacitorArray, MaximumVoltage
from camj.sim_core.sw_utils import build_sw_graph

from examples.sensors_20.mapping import mapping_function
from examples.sensors_20.sw import sw_pipeline

def analog_config():

    analog_arrays = []

    pixel_array = AnalogArray(
        name = "PixelArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(2, 160, 1)],
        num_output = (2, 160, 1)
    )
    pixel = AnalogComponent(
        name = "APS-4T",
        input_domain =[ProcessDomain.OPTICAL],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (
                ActivePixelSensor(
                    # performance parameters
                    pd_capacitance = 100e-15, # F
                    pd_supply = 3.3, # V
                    dynamic_sf = False,
                    output_vs = 2.75, # V 
                    num_transistor = 4,
                    enable_cds = True,
                    fd_capacitance = 10e-15,  # [F]
                    load_capacitance = 1e-12,  # [F]
                    tech_node = 110,  # [nm]
                    pitch = 10,  # [um]
                    array_vsize = 120,
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
    pixel_array.add_component(pixel, (120, 160, 1))

    conv1_array = AnalogArray(
        name = "Conv1Array",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(2, 160, 1)],
        num_output = (1, 80, 1)
    )

    conv1 = AnalogComponent(
        name = "Conv1",
        input_domain = [ProcessDomain.VOLTAGE],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (
                PassiveSwitchedCapacitorArray(
                    capacitance_array = [1e-12, 0.5e-12, 0.5e-12, 1e-12],
                    vs_array = [3.3, 3.3, 3.3, 3.3],
                    # noise parameters
                    noise = 0.,
                ),
                2
            )
        ],
        num_input = [(2, 2, 1)],
        num_output = (1, 1, 1)
    )
    conv1_array.add_component(conv1, (1, 80, 1))

    mp1_array = AnalogArray(
        name = "MP1Array",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(2, 80, 1)],
        num_output = (1, 40, 1)
    )
    mp1 = AnalogComponent(
        name = "MP1",
        input_domain = [ProcessDomain.VOLTAGE],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (
                MaximumVoltage(
                    supply = 3.3,  # [V]
                    t_frame = 1/60,  # [s]
                    t_acomp = 20e-6,  # [s]
                    load_capacitance = 1e-12,  # [F]
                    gain = 10
                ),
                1
            )
        ],
        num_input = [(2, 2, 1)],
        num_output = (1, 1, 1)
    )

    mp1_array.add_component(mp1, (1, 40, 1))

    conv2_array = AnalogArray(
        name = "Conv2Array",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(2, 40, 1)],
        num_output = (1, 20, 1)
    )

    conv2 = AnalogComponent(
        name = "Conv2",
        input_domain = [ProcessDomain.VOLTAGE],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (
                PassiveSwitchedCapacitorArray(
                    capacitance_array = [1e-12, 0.5e-12, 0.5e-12, 1e-12],
                    vs_array = [3.3, 3.3, 3.3, 3.3],
                    # noise parameters
                    noise = 0.,
                ),
                1
            )
        ],
        num_input = [(2, 2, 1)],
        num_output = (1, 1, 1)
    )
    conv2_array.add_component(conv2, (1, 20, 1))

    mp2_array = AnalogArray(
        name = "MP2Array",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(2, 20, 1)],
        num_output = (1, 10, 1)
    )
    mp2 = AnalogComponent(
        name = "MP2",
        input_domain = [ProcessDomain.VOLTAGE],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (
                MaximumVoltage(
                    supply = 3.3,  # [V]
                    t_frame = 1/60,  # [s]
                    t_acomp = 20e-6,  # [s]
                    load_capacitance = 1e-12,  # [F]
                    gain = 10
                ),
                1
            )
        ],
        num_input = [(2, 2, 1)],
        num_output = (1, 1, 1)
    )

    mp2_array.add_component(mp2, (1, 10, 1))

    pixel_array.add_output_array(conv1_array)
    conv1_array.add_input_array(pixel_array)

    conv1_array.add_output_array(mp1_array)
    mp1_array.add_input_array(conv1_array)

    mp1_array.add_output_array(conv2_array)
    conv2_array.add_input_array(mp1_array)

    conv2_array.add_output_array(mp2_array)
    mp2_array.add_input_array(conv2_array)

    analog_arrays.append(pixel_array)
    analog_arrays.append(conv1_array)
    analog_arrays.append(mp1_array)
    analog_arrays.append(conv2_array)
    analog_arrays.append(mp2_array)

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
    print("total energy:", total_energy, "pJ")

