
# import local modules
from camj.general.enum import ProcessorLocation, ProcessDomain
from camj.digital.memory import FIFO, DoubleBuffer
from camj.digital.compute import ADC, ComputeUnit, SystolicArray

from examples.ieee_vr22.analog import analog_config

# an example of user defined hw configuration setup 
def hw_config():

    compute_op_power = 0.5 # pJ 65nm 

    hw_dict = {
        "memory" : [],
        "compute" : [],
        "analog" : []
    }

    fifo_buffer1 = FIFO(
        name = "FIFO-1",
        size = 2*640,               # save two rows of pixel array should be sufficient
        location = ProcessorLocation.COMPUTE_LAYER,
        write_energy_per_word = 3,  # write energy per word
        read_energy_per_word = 1*4, # read energy per word 
        pixels_per_write_word = 1,      # write word length, here is one pixel
        pixels_per_read_word = 4,       # read word length, here is 4 pixels
    )
    hw_dict["memory"].append(fifo_buffer1)
 
    fifo_buffer2 = FIFO(
        name = "FIFO-2",
        size = 400*320, # needs to save one resized frame with one additional row.
        location = ProcessorLocation.COMPUTE_LAYER,
        write_energy_per_word = 3,  # write energy per word
        read_energy_per_word = 1,   # read energy per word
        pixels_per_write_word = 1,      # write word length, one pixel per word
        pixels_per_read_word = 1,       # read word length, one pixel per word
    )
    hw_dict["memory"].append(fifo_buffer2)

    double_buffer = DoubleBuffer(
        name = "DoubleBuffer",
        size = (4, 4, 4096),
        write_energy_per_word = 3,
        read_energy_per_word = 1,
        pixels_per_write_word = 1,
        pixels_per_read_word = 1,
        location = ProcessorLocation.COMPUTE_LAYER,
    )
    hw_dict["memory"].append(double_buffer)

    adc = ADC(
        name = "ADC",
        output_pixels_per_cycle = (1, 4, 1),
        location = ProcessorLocation.SENSOR_LAYER,
        energy_per_pixel = 600,
    )
    adc.set_output_buffer(fifo_buffer1)
    hw_dict["compute"].append(adc)

    resize_unit = ComputeUnit(
        name = "ResizeUnit",
        location = ProcessorLocation.SENSOR_LAYER,
        input_pixels_per_cycle = [(2, 2, 1)],
        output_per_cycle = (1, 1, 1), 
        energy_per_cycle = 4 * compute_op_power,
        num_of_stages = 2,
    )
    hw_dict["compute"].append(resize_unit)

    resize_unit.set_input_buffer(fifo_buffer1)
    resize_unit.set_output_buffer(fifo_buffer2)

    eventification_unit = ComputeUnit(
        name = "Eventification",
        location = ProcessorLocation.SENSOR_LAYER,
        input_pixels_per_cycle = [(2, 1, 1), (2, 1, 1)],
        output_per_cycle = (2, 1, 1),
        energy_per_cycle = 2*compute_op_power,
        num_of_stages = 2,
    )
    hw_dict["compute"].append(eventification_unit)

    eventification_unit.set_input_buffer(fifo_buffer2)
    eventification_unit.set_output_buffer(double_buffer)

    thresholding_unit = ComputeUnit(
        name = "ThresholdingUnit",
        location = ProcessorLocation.SENSOR_LAYER,
        input_pixels_per_cycle = [(4, 1, 1), (320, 200, 1)],
        output_pixels_per_cycle = (1, 1, 1),
        energy_per_cycle = 100 * compute_op_power,
        num_of_stages = 100,
    )
    hw_dict["compute"].append(thresholding_unit)

    thresholding_unit.set_input_buffer(double_buffer)
    thresholding_unit.set_output_buffer(double_buffer)  

    in_sensor_dnn_acc = SystolicArray(
        name = "InSensorSystolicArray",
        location = ProcessorLocation.COMPUTE_LAYER,
        size_dimension = (16, 16),
        energy_per_cycle = 16 * 16 * compute_op_power,
    )
    hw_dict["compute"].append(in_sensor_dnn_acc)

    in_sensor_dnn_acc.set_input_buffer(double_buffer)
    in_sensor_dnn_acc.set_output_buffer(double_buffer)

    return hw_dict


# an example of user defined hw configuration setup 
def hw_config_w_analog():

    compute_op_power = 0.5 # pJ 65nm 

    hw_dict = {
        "memory" : [],
        "compute" : [],
        "analog" : analog_config()
    }

    double_buffer = DoubleBuffer(
        name = "DoubleBuffer",
        size = (4, 4, 4096),
        write_energy_per_word = 3,
        read_energy_per_word = 1,
        pixels_per_write_word = 1,
        pixels_per_read_word = 1,
        location = ProcessorLocation.COMPUTE_LAYER,
    )
    hw_dict["memory"].append(double_buffer)

    adc = ADC(
        name = "ADC",
        output_pixels_per_cycle = (1, 4, 1),
        location = ProcessorLocation.SENSOR_LAYER,
        energy_per_pixel = 600,
    )
    adc.set_output_buffer(double_buffer)
    hw_dict["compute"].append(adc)

    thresholding_unit = ComputeUnit(
        name = "ThresholdingUnit",
        location = ProcessorLocation.SENSOR_LAYER,
        input_pixels_per_cycle = [(4, 1, 1), (320, 200, 1)],
        output_pixels_per_cycle = (1, 1, 1),
        energy_per_cycle = 100 * compute_op_power,
        num_of_stages = 100,
    )
    hw_dict["compute"].append(thresholding_unit)

    thresholding_unit.set_input_buffer(double_buffer)
    thresholding_unit.set_output_buffer(double_buffer)  

    in_sensor_dnn_acc = SystolicArray(
        name = "InSensorSystolicArray",
        location = ProcessorLocation.COMPUTE_LAYER,
        size_dimension = (16, 16),
        energy_per_cycle = 16 * 16 * compute_op_power,
    )
    hw_dict["compute"].append(in_sensor_dnn_acc)

    in_sensor_dnn_acc.set_input_buffer(double_buffer)
    in_sensor_dnn_acc.set_output_buffer(double_buffer)

    return hw_dict
