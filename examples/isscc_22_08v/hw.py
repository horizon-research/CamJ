import os
import sys
# directory reach
parent_directory = os.path.dirname(os.getcwd())
# setting path
sys.path.append(os.path.dirname(parent_directory))

# import local modules
from camj.sim_core.enum_const import ProcessorLocation, ProcessDomain
from camj.sim_core.digital_memory import FIFO, LineBuffer
from camj.sim_core.digital_compute import ADC, ComputeUnit

from examples.isscc_22_08v.analog import analog_config

# an example of user defined hw configuration setup 
def hw_config():

    compute_op_power = 3.544

    hw_dict = {
        "memory": [],
        "compute": [],
        "analog": analog_config()
    }

    fifo_buffer1 = FIFO(
        name = "FIFO-1",
        size = 2 * 42,
        location = ProcessorLocation.COMPUTE_LAYER,
        write_energy_per_word = 3,
        read_energy_per_word = 1,
        pixel_per_write_word = 1,
        pixel_per_read_word = 1, 
    )
    hw_dict["memory"].append(fifo_buffer1)

    fifo_buffer2 = FIFO(
        name = "FIFO-2",
        size = 21 * 21 * 8,
        location = ProcessorLocation.COMPUTE_LAYER,
        write_energy_per_word = 3,
        read_energy_per_word = 1,
        pixel_per_write_word = 1,
        pixel_per_read_word = 1,
    )
    hw_dict["memory"].append(fifo_buffer2)

    fifo_buffer3 = FIFO(
        name = "FIFO-3",
        size = 2,
        location = ProcessorLocation.COMPUTE_LAYER,
        write_energy_per_word = 3,
        read_energy_per_word = 1,
        pixel_per_write_word = 1,
        pixel_per_read_word = 1,
    )
    hw_dict["memory"].append(fifo_buffer3)

    adc = ADC(
        name = "ADC",
        output_pixels_per_cycle = (2, 1, 1),
        location = ProcessorLocation.SENSOR_LAYER,
    )
    adc.set_output_buffer(fifo_buffer1)
    hw_dict["compute"].append(adc)

    mp_unit = ComputeUnit(
        name = "MPUnit",
        domain = ProcessDomain.DIGITAL,
        location = ProcessorLocation.COMPUTE_LAYER,
        input_pixels_per_cycle = [(2, 2, 1)],
        output_pixels_per_cycle = (1, 1, 1),
        energy_per_cycle = 2 * compute_op_power,
        num_of_stages = 2,
        area = 10,
    )
    mp_unit.set_input_buffer(fifo_buffer1)
    mp_unit.set_output_buffer(fifo_buffer2)
    hw_dict["compute"].append(mp_unit)

    fc_unit = ComputeUnit(
        name="FCUnit",
        domain=ProcessDomain.DIGITAL,
        location=ProcessorLocation.COMPUTE_LAYER,
        input_pixels_per_cycle = [(21, 21, 8)],
        output_pixels_per_cycle = (1, 1, 1),
        energy_per_cycle = 1 * compute_op_power,
        num_of_stages = 21 * 21 * 8,
        area = 10,
    )
    fc_unit.set_input_buffer(fifo_buffer2)
    fc_unit.set_output_buffer(fifo_buffer3)
    hw_dict["compute"].append(fc_unit)

    return hw_dict
