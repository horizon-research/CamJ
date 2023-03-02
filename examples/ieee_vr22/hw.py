
# import local modules
from camj.sim_core.enum_const import ProcessorLocation, ProcessDomain
from camj.sim_core.digital_memory import FIFO, DoubleBuffer
from camj.sim_core.digital_compute import ADC, ComputeUnit, SystolicArray

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
        write_word_length = 1,      # write word length, here is one pixel
        read_word_length = 4,       # read word length, here is 4 pixels
        write_unit = "ADC",
        read_unit = "ResizeUnit"
    )
    hw_dict["memory"].append(fifo_buffer1)
 
    fifo_buffer2 = FIFO(
        name = "FIFO-2",
        size = 400*320, # needs to save one resized frame with one additional row.
        location = ProcessorLocation.COMPUTE_LAYER,
        write_energy_per_word = 3,  # write energy per word
        read_energy_per_word = 1,   # read energy per word
        write_word_length = 1,      # write word length, one pixel per word
        read_word_length = 1,       # read word length, one pixel per word
        write_unit = "ResizeUnit",
        read_unit = "Eventification"
    )
    hw_dict["memory"].append(fifo_buffer2)

    double_buffer = DoubleBuffer(
        name = "DoubleBuffer",
        size = (4, 4, 4096),
        write_energy_per_word = 3,
        read_energy_per_word = 1,
        write_word_length = 1,
        read_word_length = 1,
        access_units = ["ConvUnit", "InSensorSystolicArray"],
        location = ProcessorLocation.COMPUTE_LAYER,
    )
    hw_dict["memory"].append(double_buffer)

    adc = ADC(
        name = "ADC",
        output_per_cycle = (4, 1, 1),
        location = ProcessorLocation.SENSOR_LAYER,
        energy_per_pixel = 600,
    )
    adc.set_output_buffer(fifo_buffer1)
    hw_dict["compute"].append(adc)

    resize_unit = ComputeUnit(
        name = "ResizeUnit",
        domain = ProcessDomain.DIGITAL,
        location = ProcessorLocation.SENSOR_LAYER,
        input_per_cycle = [(2, 2, 1)],
        output_per_cycle = (1, 1, 1), 
        energy_per_cycle = 4 * compute_op_power,
        num_of_stages = 2,
        area = 30
    )
    hw_dict["compute"].append(resize_unit)

    resize_unit.set_input_buffer(fifo_buffer1)
    resize_unit.set_output_buffer(fifo_buffer2)

    eventification_unit = ComputeUnit(
        name = "Eventification",
        domain = ProcessDomain.DIGITAL,
        location = ProcessorLocation.SENSOR_LAYER,
        input_per_cycle = [(2, 1, 1), (2, 1, 1)],
        output_per_cycle = (2, 1, 1),
        energy_per_cycle = 2*compute_op_power,
        num_of_stages = 2,
        area = 10,
    )
    hw_dict["compute"].append(eventification_unit)

    eventification_unit.set_input_buffer(fifo_buffer2)
    eventification_unit.set_output_buffer(double_buffer)

    thresholding_unit = ComputeUnit(
        name = "ThresholdingUnit",
        domain = ProcessDomain.DIGITAL,
        location = ProcessorLocation.SENSOR_LAYER,
        input_per_cycle = [(4, 1, 1), (320, 200, 1)],
        output_per_cycle = (1, 1, 1),
        energy_per_cycle = 100*compute_op_power,
        area = 10,
        num_of_stages = 640,
    )
    hw_dict["compute"].append(thresholding_unit)

    thresholding_unit.set_input_buffer(double_buffer)
    thresholding_unit.set_output_buffer(double_buffer)  

    in_sensor_dnn_acc = SystolicArray(
        name = "InSensorSystolicArray",
        domain = ProcessDomain.DIGITAL,
        location = ProcessorLocation.COMPUTE_LAYER,
        size_dimension = (16, 16),
        energy_per_cycle = 16 * 16 * compute_op_power,
        area = 160
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
        name="DoubleBuffer",
        size=(4, 4, 4096),
        clock = 500,    # MHz
        read_port = 16,
        write_port = 16,
        read_write_port = 16,
        write_energy = 3,
        read_energy = 1,
        access_units = ["ConvUnit", "InSensorSystolicArray", "ThresholdingUnit", "ADC"],
        location = ProcessorLocation.COMPUTE_LAYER,
    )
    hw_dict["memory"].append(double_buffer)

    adc = ADC(
        name = "ADC",
        output_throughput = (320, 1, 1),
        location = ProcessorLocation.SENSOR_LAYER,
    )
    adc.set_output_buffer(double_buffer)
    hw_dict["compute"].append(adc)

    thresholding_unit = ComputeUnit(
        name="ThresholdingUnit",
        domain=ProcessDomain.DIGITAL,
        location=ProcessorLocation.SENSOR_LAYER,
        input_throughput = [(4, 1, 1), (320, 200, 1)],
        output_throughput = (1, 1, 1), 
        clock = 500, # MHz
        energy = 320*200*compute_op_power,
        area = 10,
        initial_delay = 0,
        delay = 640,
    )
    hw_dict["compute"].append(thresholding_unit)

    thresholding_unit.set_input_buffer(double_buffer)
    thresholding_unit.set_output_buffer(double_buffer)  

    in_sensor_dnn_acc = SystolicArray(
        name="InSensorSystolicArray",
        domain=ProcessDomain.DIGITAL,
        location=ProcessorLocation.COMPUTE_LAYER,
        size_dimension=(16, 16),
        clock=500,
        energy=16*16*compute_op_power,
        area=160
    )
    hw_dict["compute"].append(in_sensor_dnn_acc)

    in_sensor_dnn_acc.set_input_buffer(double_buffer)
    in_sensor_dnn_acc.set_output_buffer(double_buffer)

    return hw_dict
