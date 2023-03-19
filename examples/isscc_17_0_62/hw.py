
# import local modules
from camj.digital.compute import ADC, ComputeUnit, SystolicArray
from camj.digital.memory import FIFO, DoubleBuffer
from camj.general.enum import ProcessorLocation, ProcessDomain

# import customized configs
from examples.isscc_17_0_62.analog import analog_config


def hw_config():

    compute_op_power = 0.28

    hw_dict = {
        "memory": [],
        "compute": [],
        "analog" : analog_config()
    }

    double_buffer = DoubleBuffer(
        name = "DoubleBuffer",
        size = (4, 4096, 4096),
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

    mp_unit = ComputeUnit(
        name = "MPUnit",
        domain = ProcessDomain.DIGITAL,
        location = ProcessorLocation.COMPUTE_LAYER,
        input_pixels_per_cycle = [(2, 16, 1)],
        output_pixels_per_cycle = (1, 8, 1),
        energy_per_cycle = 3 * 8 * compute_op_power,
        num_of_stages = 2,
        area = 10
    )
    mp_unit.set_input_buffer(double_buffer)
    mp_unit.set_output_buffer(double_buffer)
    hw_dict["compute"].append(mp_unit)

    in_sensor_dnn_acc = SystolicArray(
        name = "InSensorSystolicArray",
        domain = ProcessDomain.DIGITAL,
        location = ProcessorLocation.COMPUTE_LAYER,
        size_dimension = (32, 32),
        energy_per_cycle = 32 * 32 * 2 * compute_op_power,
        area = 160
    )
    hw_dict["compute"].append(in_sensor_dnn_acc)

    in_sensor_dnn_acc.set_input_buffer(double_buffer)
    in_sensor_dnn_acc.set_output_buffer(double_buffer)

    return hw_dict
