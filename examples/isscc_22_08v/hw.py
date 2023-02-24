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
        name="FIFO1",
        hw_impl = "sram",
        count = 2*1,
        clock = 500,    # MHz
        write_energy = 3,
        read_energy = 1,
        location = ProcessorLocation.COMPUTE_LAYER,
        duplication = 42,
        write_unit = "ADC",
        read_unit = "MPUnit"
    )
    hw_dict["memory"].append(fifo_buffer1)

    fifo_buffer2 = FIFO(
        name="FIFO2",
        hw_impl = "sram",
        count = 21*8,
        clock = 500,    # MHz
        write_energy = 3,
        read_energy = 1,
        location = ProcessorLocation.COMPUTE_LAYER,
        duplication = 21,
        write_unit = "MPUnit",
        read_unit = "FCUnit",
    )
    hw_dict["memory"].append(fifo_buffer2)

    fifo_buffer3 = FIFO(
        name="FIFO3",
        hw_impl = "sram",
        count = 2,
        clock = 500,    # MHz
        write_energy = 3,
        read_energy = 1,
        location = ProcessorLocation.COMPUTE_LAYER,
        duplication = 1,
        write_unit = "FCUnit",
        read_unit = None
    )
    hw_dict["memory"].append(fifo_buffer3)

    adc = ADC(
        name = "ADC",
        output_throughput = (42, 1, 1),
        location = ProcessorLocation.SENSOR_LAYER,
    )
    adc.set_output_buffer(fifo_buffer1)
    hw_dict["compute"].append(adc)

    mp_unit = ComputeUnit(
        name="MPUnit",
        domain=ProcessDomain.DIGITAL,
        location=ProcessorLocation.COMPUTE_LAYER,
        input_throughput = [(42, 2, 1)],
        output_throughput = (21, 1, 1),
        clock = 500, # MHz
        energy = 3*21*compute_op_power,
        area = 10,
        initial_delay = 0,
        delay = 1,
    )
    mp_unit.set_input_buffer(fifo_buffer1)
    mp_unit.set_output_buffer(fifo_buffer2)
    hw_dict["compute"].append(mp_unit)

    fc_unit = ComputeUnit(
        name="FCUnit",
        domain=ProcessDomain.DIGITAL,
        location=ProcessorLocation.COMPUTE_LAYER,
        input_throughput = [(21, 21, 8)],
        output_throughput = (1, 1, 1),
        clock = 500, # MHz
        energy = 3*21*compute_op_power,
        area = 10,
        initial_delay = 0,
        delay = 1,
    )
    fc_unit.set_input_buffer(fifo_buffer2)
    fc_unit.set_output_buffer(fifo_buffer3)
    hw_dict["compute"].append(fc_unit)

    return hw_dict
