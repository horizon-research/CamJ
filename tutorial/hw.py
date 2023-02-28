
# import local modules
from camj.sim_core.enum_const import ProcessorLocation, ProcessDomain
from camj.sim_core.digital_memory import FIFO, LineBuffer
from camj.sim_core.digital_compute import ADC, ComputeUnit

from tutorial.analog import analog_config

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
        size = (3, 32),  # can 3x 32 number of pixels
        location = ProcessorLocation.COMPUTE_LAYER,
        write_energy_per_word = 3,  # 3pJ to write a word
        read_energy_per_word = 1,   # 1pJ to read a word
        write_word_length = 1,      # the word length or #pixel per write access
        read_word_length = 1,       # the word length or #pixel per read access
        write_unit = "ADC",
        read_unit = "ConvUnit"
    )
    hw_dict["memory"].append(line_buffer)

    fifo_buffer1 = FIFO(
        name="FIFO-1",
        size = 32,
        location = ProcessorLocation.COMPUTE_LAYER,
        write_energy_per_word = 3,  # 3pJ to write a word
        read_energy_per_word = 1,   # 1pJ to read a word
        write_word_length = 1,      # the word length or #pixel per write access
        read_word_length = 1,       # the word length or #pixel per read access
        write_unit = "ConvUnit",
        read_unit = "AbsUnit"
    )
    hw_dict["memory"].append(fifo_buffer1)

    fifo_buffer2 = FIFO(
        name="FIFO-2",
        size = 32*32,
        location = ProcessorLocation.COMPUTE_LAYER,
        write_energy_per_word = 3,  # 3pJ to write a word
        read_energy_per_word = 1,   # 1pJ to read a word
        write_word_length = 1,      # the word length or #pixel per write access
        read_word_length = 1,       # the word length or #pixel per read access 
        write_unit = "AbsUnit",
        read_unit = "AbsUnit"
    )
    hw_dict["memory"].append(fifo_buffer2)

    adc = ADC(
        name = "ADC",
        output_per_cycle = (32, 1, 1),
        location = ProcessorLocation.SENSOR_LAYER,
    )
    adc.set_output_buffer(line_buffer)
    hw_dict["compute"].append(adc)

    conv_unit = ComputeUnit(
        name="ConvUnit",
        domain=ProcessDomain.DIGITAL,
        location=ProcessorLocation.SENSOR_LAYER,
        input_per_cycle = [(1, 3, 1)],
        output_per_cycle = (1, 1, 1), 
        energy_per_cycle = 9*compute_op_power,
        num_of_stages = 3,
        area = 30
    )
    hw_dict["compute"].append(conv_unit)

    conv_unit.set_input_buffer(line_buffer)
    conv_unit.set_output_buffer(fifo_buffer1)

    abs_unit = ComputeUnit(
        name="AbsUnit",
        domain=ProcessDomain.DIGITAL,
        location=ProcessorLocation.SENSOR_LAYER,
        input_per_cycle = [(1, 1, 1)],
        output_per_cycle = (1, 1, 1), 
        energy_per_cycle = 1*compute_op_power,
        num_of_stages = 1,
        area = 10
    )
    hw_dict["compute"].append(abs_unit)

    abs_unit.set_input_buffer(fifo_buffer1)
    abs_unit.set_output_buffer(fifo_buffer2)

    return hw_dict

