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
from camj.sim_core.pixel_libs import DigitalPixelSensor
from camj.sim_core.analog_libs import GeneralCircuit
from camj.sim_core.sw_utils import build_sw_graph

from examples.vlsi_21.mapping import mapping_function
from examples.vlsi_21.sw import sw_pipeline

def analog_config():

    analog_arrays = []

    pixel_array = AnalogArray(
        name = "PixelArray",
        layer = ProcessorLocation.SENSOR_LAYER,
        num_input = [(1668, 1364, 1)],
        num_output = (1668, 1364, 1)
    )
    pixel = AnalogComponent(
        name = "DPSPixel",
        input_domain =[ProcessDomain.OPTICAL],
        output_domain = ProcessDomain.VOLTAGE,
        component_list = [
            (
                DigitalPixelSensor(
                    # performance parameters
                    pd_capacitance = 100e-15, # [F]
                    pd_supply = 2.8, # [V]
                    dynamic_sf = False,
                    output_vs = 2.4,  # output voltage swing [V]
                    num_transistor = 4,
                    enable_cds = True,
                    fd_capacitance = 10e-15,  # [F]
                    load_capacitance = 200e-15,  # [F]
                    tech_node = 130,  # [um]
                    pitch = 4,  # [um]
                    array_vsize = 0, # pixel array vertical size
                    # ADC performance parameters
                    adc_type = 'SS',
                    adc_fom = 4300e-15,  # [J/conversion]
                    adc_reso = 10,
                    # noise parameters
                    dark_current_noise = 0.,
                    enable_dcnu = False,
                    enable_prnu = False,
                    dcnu_std = 0.001,
                    # FD parameters
                    fd_gain = 1.0,
                    fd_noise = 0.,
                    fd_prnu_std = 0.001,
                    # SF parameters
                    sf_gain = 1.0,
                    sf_noise = 0.,
                    sf_prnu_std = 0.001,
                    # CDS parameters
                    cds_gain = 1.0,
                    cds_noise = 0.,
                    cds_prnu_std = 0.001,
                    # ADC parameters
                    adc_noise = 0.,
                ),
                1
            ),
            (
                GeneralCircuit(
                    supply = 2.8,  # [V]
                    t_operation = 1.04e-3,  # [s]
                    i_dc = 20e-9,  # [s]
                ),
                2*2*2
            ),
        ],
        num_input = [(1, 1, 1)],
        num_output = (1, 1, 1)
    )

    pixel_array.add_component(pixel, (1668, 1364, 1))
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

    total_energy = launch_analog_simulation(analog_arrays, sw_stage_list, mapping_dict)
    print("total energy:", total_energy)

