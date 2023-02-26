
# import local modules
from camj.sim_core.enum_const import ProcessorLocation, ProcessDomain
from camj.sim_core.digital_memory import FIFO, LineBuffer
from camj.sim_core.digital_compute import ADC, ComputeUnit, SystolicArray

from tutorial.analog_config import analog_config

# an example of user defined hw configuration setup 
def hw_config():

    compute_op_power = 0.5 # pJ 65nm 

    hw_dict = {
        "memory" : [],
        "compute" : [],
        "analog" : analog_config()
    }
 
    line_buffer = LineBuffer(
        name="LineBuffer",
        hw_impl = "sram",
        size = (32, 32),
        clock = 500,    # MHz
        write_energy = 3,
        read_energy = 1,
        location = ProcessorLocation.COMPUTE_LAYER,
        duplication = 1,
        write_unit = "ADC",
        read_unit = "ConvUnit"
    )
    hw_dict["memory"].append(line_buffer)

    fifo_buffer2 = FIFO(
        name="FIFO-2",
        hw_impl = "sram",
        count = 32*32,
        clock = 500,    # MHz
        write_energy = 3,
        read_energy = 1,
        location = ProcessorLocation.COMPUTE_LAYER,
        duplication = 8,
        write_unit = "ConvUnit",
        read_unit = "AbsUnit"
    )
    hw_dict["memory"].append(fifo_buffer2)

    fifo_buffer3 = FIFO(
        name="FIFO-3",
        hw_impl = "sram",
        count = 32*32,
        clock = 500,    # MHz
        write_energy = 3,
        read_energy = 1,
        location = ProcessorLocation.COMPUTE_LAYER,
        duplication = 8,
        write_unit = "AbsUnit",
        read_unit = "AbsUnit"
    )
    hw_dict["memory"].append(fifo_buffer3)

    adc = ADC(
        name = "ADC",
        output_throughput = (32, 1, 1),
        location = ProcessorLocation.SENSOR_LAYER,
    )
    adc.set_output_buffer(line_buffer)
    hw_dict["compute"].append(adc)

    conv_unit = ComputeUnit(
        name="ConvUnit",
        domain=ProcessDomain.DIGITAL,
        location=ProcessorLocation.SENSOR_LAYER,
        input_throughput = [(32, 3, 1)],
        output_throughput = (32, 1, 8), 
        clock = 500, # MHz
        energy = 32*9*compute_op_power,
        area = 30,
        initial_delay = 0,
        delay = 3,
    )
    hw_dict["compute"].append(conv_unit)

    conv_unit.set_input_buffer(line_buffer)
    conv_unit.set_output_buffer(fifo_buffer2)

    abs_unit = ComputeUnit(
        name="AbsUnit",
        domain=ProcessDomain.DIGITAL,
        location=ProcessorLocation.SENSOR_LAYER,
        input_throughput = [(32, 1, 8)],
        output_throughput = (32, 1, 8), 
        clock = 500, # MHz
        energy = 32*1*compute_op_power,
        area = 10,
        initial_delay = 0,
        delay = 3,
    )
    hw_dict["compute"].append(abs_unit)

    abs_unit.set_input_buffer(fifo_buffer2)
    abs_unit.set_output_buffer(fifo_buffer3)

    return hw_dict

