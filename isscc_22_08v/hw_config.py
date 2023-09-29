import os
import sys

# directory reach
directory = os.getcwd()
parent_directory = os.path.dirname(directory)
# setting path
sys.path.append(os.path.dirname(directory))
sys.path.append(os.path.dirname(parent_directory))

# import local modules
from enum_const import ProcessorLocation, ProcessDomain
from memory import FIFO, LineBuffer
from hw_compute import ADC, ComputeUnit


# an example of user defined hw configuration setup 
def hw_config():
    hw_dict = {
        "memory": [],
        "compute": [],
    }

    fifo_buffer1 = FIFO(
        name="FIFO1",
        hw_impl="sram",
        count=9 * 2,
        clock=500,  # MHz
        write_energy=3,
        read_energy=1,
        location=ProcessorLocation.COMPUTE_LAYER,
        duplication=42,
        write_unit="ADC",
        read_unit="ConvUnit"
    )
    hw_dict["memory"].append(fifo_buffer1)

    fifo_buffer2 = FIFO(
        name="FIFO2",
        hw_impl="sram",
        count=8 * 2,
        clock=500,  # MHz
        write_energy=3,
        read_energy=1,
        location=ProcessorLocation.COMPUTE_LAYER,
        duplication=42,
        write_unit="ConvUnit",
        read_unit="MPunit"
    )
    hw_dict["memory"].append(fifo_buffer2)

    fifo_buffer3 = FIFO(
        name="FIFO3",
        hw_impl="sram",
        count=21 * 8,
        clock=500,  # MHz
        write_energy=3,
        read_energy=1,
        location=ProcessorLocation.COMPUTE_LAYER,
        duplication=21,
        write_unit="MPUnit",
        read_unit=None
    )
    hw_dict["memory"].append(fifo_buffer3)

    adc = ADC(
        name="ADC",
        type=1,  # this needs to be fixed, use some enum.
        pixel_adc_ratio=(1, 126, 1),
        output_throughput=(126, 1, 1),  # redundent
        location=ProcessorLocation.SENSOR_LAYER,
    )
    adc.set_output_buffer(fifo_buffer1)
    hw_dict["compute"].append(adc)

    conv_unit = ComputeUnit(
        name="ConvUnit",
        domain=ProcessDomain.DIGITAL,
        location=ProcessorLocation.SENSOR_LAYER,
        input_throughput=[(3 * 21, 3 * 2, 1)],
        output_throughput=(21, 2, 8),
        clock=500,  # MHz
        energy=(3 * 3 * 8 * 21 * 2) * 4.6,
        area=10,
        initial_delay=0,
        delay=3 * 8,
    )
    hw_dict["compute"].append(conv_unit)

    conv_unit.set_input_buffer(fifo_buffer1)
    conv_unit.set_output_buffer(fifo_buffer2)

    mp_unit = ComputeUnit(
        name="MPUnit",
        domain=ProcessDomain.DIGITAL,
        location=ProcessorLocation.COMPUTE_LAYER,
        input_throughput=[(42, 2, 8)],
        output_throughput=(21, 1, 8),
        clock=500,  # MHz
        energy=3 * 21 * 4.6,
        area=10,
        initial_delay=0,
        delay=1,
    )
    mp_unit.set_input_buffer(fifo_buffer2)
    mp_unit.set_output_buffer(fifo_buffer3)
    hw_dict["compute"].append(mp_unit)

    return hw_dict
