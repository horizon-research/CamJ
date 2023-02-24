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
        hw_impl = "sram",
        count = 16,
        clock = 500,    # MHz
        write_energy = 3,
        read_energy = 1,
        location = ProcessorLocation.COMPUTE_LAYER,
        duplication = 16,
        write_unit = "ADC",
        read_unit = "FCUnit"
    )
    hw_dict["memory"].append(fifo_buffer1)

    fifo_buffer2 = FIFO(
        name="FIFO2",
        hw_impl = "sram",
        count = 10,
        clock = 500,    # MHz
        write_energy = 3,
        read_energy = 1,
        location = ProcessorLocation.COMPUTE_LAYER,
        duplication = 10,
        write_unit = "FCUnit",
        read_unit = None
    )
    hw_dict["memory"].append(fifo_buffer2)

    adc = ADC(
        name = "ADC",
        output_throughput = (1, 1, 16),
        location = ProcessorLocation.SENSOR_LAYER,
    )
    adc.set_output_buffer(fifo_buffer1)
    hw_dict["compute"].append(adc)

    fc_unit = ComputeUnit(
        name="FCUnit",
        domain=ProcessDomain.DIGITAL,
        location=ProcessorLocation.COMPUTE_LAYER,
        input_throughput = [(1, 1, 16)],
        output_throughput = (1, 1, 10),
        clock = 500, # MHz
        energy = 16*10*compute_op_power,
        area = 10,
        initial_delay = 0,
        delay = 1,
    )
    fc_unit.set_input_buffer(fifo_buffer1)
    fc_unit.set_output_buffer(fifo_buffer2)
    hw_dict["compute"].append(fc_unit)

    return hw_dict
