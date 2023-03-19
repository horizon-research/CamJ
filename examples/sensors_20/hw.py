import os
import sys
# directory reach
parent_directory = os.path.dirname(os.getcwd())
# setting path
sys.path.append(os.path.dirname(parent_directory))

# import local modules
from camj.general.enum import ProcessorLocation, ProcessDomain
from camj.digital.memory import FIFO, LineBuffer
from camj.digital.compute import ADC, ComputeUnit

# import customized configs
from examples.sensors_20.analog import analog_config
 
def hw_config():

    compute_op_power = 3.544

    hw_dict = {
        "memory": [],
        "compute": [],
        "analog": analog_config()
    }

    fifo_buffer1 = FIFO(
        name = "FIFO-1",
        size = 80,
        location = ProcessorLocation.COMPUTE_LAYER,
        write_energy_per_word = 3,
        read_energy_per_word = 1,
        pixels_per_write_word = 1,
        pixels_per_read_word = 1, 
    )
    hw_dict["memory"].append(fifo_buffer1)

    fifo_buffer2 = FIFO(
        name = "FIFO-2",
        size = 1,
        location = ProcessorLocation.COMPUTE_LAYER,
        write_energy_per_word = 3,
        read_energy_per_word = 1,
        pixels_per_write_word = 1,
        pixels_per_read_word = 1,
    )
    hw_dict["memory"].append(fifo_buffer2)

    adc = ADC(
        name = "ADC",
        output_pixels_per_cycle = (2, 1, 1),
        location = ProcessorLocation.SENSOR_LAYER,
    )
    adc.set_output_buffer(fifo_buffer1)
    hw_dict["compute"].append(adc)

    fc_unit = ComputeUnit(
        name="FCUnit",
        domain=ProcessDomain.DIGITAL,
        location=ProcessorLocation.COMPUTE_LAYER,
        input_pixels_per_cycle = [(1, 1, 10)],
        output_pixels_per_cycle = (1, 1, 1),
        energy_per_cycle = 1 * compute_op_power,
        num_of_stages = 1 * 1 * 10,
        area = 10,
    )
    fc_unit.set_input_buffer(fifo_buffer1)
    fc_unit.set_output_buffer(fifo_buffer2)
    hw_dict["compute"].append(fc_unit)

    return hw_dict
