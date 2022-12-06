import os
import sys

# directory reach
directory = os.getcwd()
parent_directory = os.path.dirname(directory)
# setting path
sys.path.append(os.path.dirname(directory))
sys.path.append(os.path.dirname(parent_directory))

from analog_infra import AnalogArray, AnalogUnit, AnalogComponent
from enum_const import ProcessorLocation, ProcessDomain
from analog_utils import check_analog_connect_consistency, compute_total_energy
from acomp_library import *


def dummy_energy_func():
    return 1


def analog_config():
    analog_arrays = []

    pixel_array = AnalogArray(
        name="PixelArray",
        layer=ProcessorLocation.SENSOR_LAYER,
        num_input=[(3, 126)],
        num_output=(3, 126)
    )
    pixel = AnalogUnit(
        name="Pxiel",
        input_domain=[ProcessDomain.OPTICAL],
        output_domain=ProcessDomain.TIME,
        energy=PWM(pd_capacitance=10e-12, pd_supply=0.8, ramp_capacitance=1e-12, gate_capacitance=10e-15,
                   num_readout=8).energy()
    )

    pixel_array.add_unit(pixel, (126, 126))
    pixel_array.set_source_unit([pixel])
    pixel_array.set_destination_unit([pixel])

    analog_weight = AnalogArray(
        name="AnalogWeight",
        layer=ProcessorLocation.SENSOR_LAYER,
        num_input=None,
        num_output=(3, 3)
    )
    current_dac = AnalogUnit(
        name="CurrentDAC",
        input_domain=[ProcessDomain.DIGITAL],
        output_domain=ProcessDomain.CURRENT,
        energy=dac_d_to_c(supply=0.8, load_capacitance=2e-12, t_readout=7.9e-6, resolution=3,
                          num_current_path=1).energy()
    )

    analog_weight.add_unit(current_dac, (3, 3))
    analog_weight.set_source_unit([current_dac])
    analog_weight.set_destination_unit([current_dac])

    pe_array = AnalogArray(
        name="PEArray",
        layer=ProcessorLocation.SENSOR_LAYER,
        num_input=[(3, 3), (3, 126)],
        num_output=(1, 42)
    )

    pe = AnalogUnit(
        name="PE",
        input_domain=[ProcessDomain.CURRENT, ProcessDomain.TIME],
        output_domain=ProcessDomain.DIGITAL,
        energy=None,
        num_input=[(3, 3), (3, 3)],
        num_output=(1, 1)
    )

    pe_array.add_unit(pe, (1, 42))

    sci = AnalogComponent(
        name="SCI",
        input_domain=[ProcessDomain.CURRENT, ProcessDomain.TIME],
        output_domain=ProcessDomain.CHARGE,
        energy=dac_d_to_c(supply=0.8, load_capacitance=2e-12, t_readout=7.9e-6, resolution=3,
                          num_current_path=1).energy()
    )
    pe.add_component(sci, (3, 3))

    capacitor = AnalogComponent(
        name="Capacitor",
        input_domain=[ProcessDomain.CHARGE],
        output_domain=ProcessDomain.VOLTAGE,
        energy=AnalogMemory(type='passive', capacitance=2e-12, supply=0.8, droop_rate=0, t_sample=0, t_hold=0,
                            resolution=0, gain_opamp=0).energy()
    )
    pe.add_component(capacitor, (9, 4))

    comparator = AnalogComponent(
        name="Comparator",
        input_domain=[ProcessDomain.VOLTAGE],
        output_domain=ProcessDomain.DIGITAL,
        energy=Comparator(supply=0.8, i_bias=10e-6, t_readout=10e-9).energy()
    )

    pe.add_component(comparator, (1, 1))

    capacitor.add_input_component(sci)
    sci.add_output_component(capacitor)

    capacitor.add_output_component(comparator)
    comparator.add_input_component(capacitor)

    pe.set_source_component([sci])
    pe.set_destination_component([comparator])

    pe_array.set_source_unit([pe])
    pe_array.set_destination_unit([pe])

    pe_array.add_input_array(pixel_array)
    pe_array.add_input_array(analog_weight)

    pixel_array.add_output_array(pe_array)
    analog_weight.add_output_array(pe_array)

    analog_arrays.append(pixel_array)
    analog_arrays.append(analog_weight)
    analog_arrays.append(pe_array)

    return analog_arrays


if __name__ == '__main__':
    analog_arrays = analog_config()

    check_analog_connect_consistency(analog_arrays)

    total_energy = compute_total_energy(analog_arrays)
    print("total energy:", total_energy)
