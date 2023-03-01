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

from examples.tcas_i22.analog import analog_config

# an example of user defined hw configuration setup 
def hw_config():

    compute_op_power = 3.544

    hw_dict = {
        "memory": [],
        "compute": [],
        "analog": analog_config()
    }

    fifo_buffer1 = FIFO(
        name="FIFO1",
        size = 16,
        location = ProcessorLocation.COMPUTE_LAYER,
        write_energy_per_word = 3,
        read_energy_per_word = 1,
        write_word_length = 1,
        read_word_length = 1,
        write_unit = "ADC",
        read_unit = "FCUnit"
    )
    hw_dict["memory"].append(fifo_buffer1)

    fifo_buffer2 = FIFO(
        name = "FIFO2",
        size = 10,
        location = ProcessorLocation.COMPUTE_LAYER,
        write_energy_per_word = 3,
        read_energy_per_word = 1,
        write_word_length = 1,
        read_word_length = 1,
        write_unit = "FCUnit",
        read_unit = None
    )
    hw_dict["memory"].append(fifo_buffer2)

    adc = ADC(
        name = "ADC",
        output_per_cycle = (1, 1, 1),
        location = ProcessorLocation.SENSOR_LAYER,
    )
    adc.set_output_buffer(fifo_buffer1)
    hw_dict["compute"].append(adc)

    fc_unit = ComputeUnit(
        name = "FCUnit",
        domain = ProcessDomain.DIGITAL,
        location = ProcessorLocation.COMPUTE_LAYER,
        input_per_cycle = [(1, 1, 16)],
        output_per_cycle = (1, 1, 10),
        energy_per_cycle = 10*compute_op_power,
        area = 10,
        num_of_stages = 16
    )
    fc_unit.set_input_buffer(fifo_buffer1)
    fc_unit.set_output_buffer(fifo_buffer2)
    hw_dict["compute"].append(fc_unit)

    return hw_dict
