
# import local modules
from camj.general.enum import ProcessorLocation, ProcessDomain
from camj.digital.memory import FIFO, DoubleBuffer
from camj.digital.compute import ADC, ComputeUnit, SystolicArray


# an example of user defined hw configuration setup 
def hw_config():

    compute_op_power = 1

    hw_dict = {
        "memory": [],
        "compute": [],
        "analog": [],
    }

    double_buffer = DoubleBuffer(
        name = "DoubleBuffer",
        size = (1, 1, 1280),
        write_energy_per_word = 3,
        read_energy_per_word = 1,
        pixels_per_write_word = 1,
        pixels_per_read_word = 1,
        location = ProcessorLocation.COMPUTE_LAYER,
    )
    hw_dict["memory"].append(double_buffer)

    adc = ADC(
        name = "ADC",
        output_pixels_per_cycle = (1, 4, 3),
        location = ProcessorLocation.COMPUTE_LAYER,
        energy_per_pixel = 600,
    )
    adc.set_output_buffer(double_buffer)
    hw_dict["compute"].append(adc)

    comp_unit = ComputeUnit(
        name="CompUnit",
        location=ProcessorLocation.COMPUTE_LAYER,
        input_pixels_per_cycle = [(1, 32, 3)],
        output_pixels_per_cycle = (1, 8, 1),
        energy_per_cycle = 8*compute_op_power,
        num_of_stages = 4,
    )
    comp_unit.set_input_buffer(double_buffer)
    comp_unit.set_output_buffer(double_buffer)
    hw_dict["compute"].append(comp_unit)

    sampler_unit = ComputeUnit(
        name="SampleUnit",
        location=ProcessorLocation.COMPUTE_LAYER,
        input_pixels_per_cycle = [(1, 16, 3)],
        output_pixels_per_cycle = (1, 8, 3),
        energy_per_cycle = 8*compute_op_power,
        num_of_stages = 2,
    )
    sampler_unit.set_input_buffer(double_buffer)
    sampler_unit.set_output_buffer(double_buffer)
    hw_dict["compute"].append(sampler_unit)

    return hw_dict
