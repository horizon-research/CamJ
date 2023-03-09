import os
import sys
import numpy as np

# setting path
sys.path.append(os.path.dirname(os.getcwd()))

from camj.sim_core.analog_libs import MaximumVoltage, PassiveAverage, Adder, Subtractor,\
                                      AbsoluteDifference, Voltage2VoltageConv

def test_maximum_voltage():

    max_voltage_comp = MaximumVoltage(
        supply = 1.8,  # [V]
        t_frame = 30e-3,  # [s]
        t_acomp = 1e-6,  # [s]
        load_capacitance = 1e-12,  # [F]
        gain = 10,
        # noise parameters
        noise = 0.0,
    )

    # set dummy input array
    input_signal_list = []

    for i in range(1, 4):
        input_signal_list.append(
            np.ones((5, 5)) * i
        )

    output_result = max_voltage_comp.noise(input_signal_list)

    assert output_result[1][0].shape == (5, 5), "The max output should be a shape of (5, 5)"
    assert np.mean(output_result[1][0]) == 3, "The max value of output should be 3, got %f" % np.mean(output_result[1])

def test_passive_average():

    passive_average_comp = PassiveAverage(
        # peformance parameters
        capacitance_array = [1e-12, 1e-12, 1e-12, 1e-12, 1e-12],
        vs_array = [3.3, 3.3, 3.3, 3.3, 3.3],
        sf_load_capacitance = 1e-12,  # [F]
        sf_supply = 1.8,  # [V]
        sf_output_vs = 1,  # [V]
        sf_bias_current = 5e-6,  # [A]
        # noise parameters
        psca_noise = 0.,
        sf_gain = 1.0,
        sf_noise = 0.,
        sf_enable_prnu = False,
        sf_prnu_std = 0.001,
    )

    input_signal_list = []

    for i in range(1, 6):
        input_signal_list.append(
            np.ones((10, 10)) * i
        )

    output_signal = passive_average_comp.noise(input_signal_list)

    assert output_signal[1][0].shape == (10, 10), "The max output should be a shape of (10, 10)"
    assert np.mean(output_signal[1][0]) == 3, "The max value of output should be 3, got %f" % np.mean(output_signal[1])

def test_adder():
    adder_comp = Adder(
        # performance parameters
        load_capacitance = 1e-12,  # [F]
        input_capacitance = 1e-12,  # [F]
        t_sample = 2e-6,  # [s]
        t_frame = 10e-3,  # [s]
        supply = 1.8,  # [V]
        gain_open = 256,
        differential = False,
        # noise parameters
        columnwise_op = True,
        noise = 0.,
        enable_prnu = False,
        prnu_std = 0.001
    )

    input_signal_list = []

    for i in range(4, 6):
        input_signal_list.append(
            np.ones((10, 10)) * i
        )

    output_signal = adder_comp.noise(input_signal_list)

    assert output_signal[1][0].shape == (10, 10), "The max output should be a shape of (10, 10)"
    assert np.mean(output_signal[1][0]) == 9, "The max value of output should be 9.0, got %f" % np.mean(output_signal[1])

def test_subtractor():
    sub_comp = Subtractor(
        # performance parameters
        load_capacitance = 1e-12,  # [F]
        input_capacitance = 1e-12,  # [F]
        t_sample = 2e-6,  # [s]
        t_frame = 10e-3,  # [s]
        supply = 1.8,  # [V]
        gain_open = 256,
        differential = False,
        # noise parameters
        columnwise_op = True,
        noise = 0.,
        enable_prnu = False,
        prnu_std = 0.001
    )

    input_signal_list = []

    input_signal_list.append(
        np.ones((10, 10)) * 9
    )
    input_signal_list.append(
        np.ones((10, 10)) * 3
    )
    output_signal = sub_comp.noise(input_signal_list)

    assert output_signal[1][0].shape == (10, 10), "The max output should be a shape of (10, 10)"
    assert np.mean(output_signal[1][0]) == 6, "The max value of output should be 6.0, got %f" % np.mean(output_signal[1])

def test_abs():
    abs_comp = AbsoluteDifference(
        # performance parameters
        load_capacitance = 1e-12,  # [F]
        input_capacitance = 1e-12,  # [F]
        t_sample = 2e-6,  # [s]
        t_frame = 10e-3,  # [s]
        supply = 1.8,  # [V]
        gain_open = 256,
        differential = False,
        # noise parameters
        noise = 0.,
        enable_prnu = False,
        prnu_std = 0.001
    )

    input_signal_list = []

    input_signal_list.append(
        np.ones((10, 10)) * 4
    )
    input_signal_list.append(
        np.ones((10, 10)) * 9
    )
    output_signal = abs_comp.noise(input_signal_list)

    assert output_signal[1][0].shape == (10, 10), "The max output should be a shape of (10, 10)"
    assert np.mean(output_signal[1][0]) == 5, "The max value of output should be 5.0, got %f" % np.mean(output_signal[1])

def test_v2v_conv():
    v2v_conv_comp = Voltage2VoltageConv(
        # peformance parameters
        capacitance_array = [1e-12] * 9,
        vs_array = [3.3] * 9,
        sf_load_capacitance = 1e-12,  # [F]
        sf_supply = 1.8,  # [V]
        sf_output_vs = 1,  # [V]
        sf_bias_current = 5e-6,  # [A]
        # noise parameters
        psca_noise = 0.,
        sf_gain = 1.0,
        sf_noise = 0.,
        sf_enable_prnu = False,
        sf_prnu_std = 0.001,
    )
    num_kernel = 3

    input_signal_list = []
    # first add a dummy input
    input_signal_list.append(
        np.ones((128, 128))
    )
    # then add some weights
    for i in range(num_kernel):
        input_signal_list.append(
            np.array(
                [
                    [1, 1, 1],
                    [1, 1, 1],
                    [1, 1, 1]
                ]
            ) * (i+1)
        )

    v2v_conv_comp.set_conv_config(
        kernel_size = [(3, 3, 1)],
        num_kernel = [num_kernel],
        stride = [(1, 1, 1)]
    )

    _, output_signal = v2v_conv_comp.noise(input_signal_list)

    assert len(output_signal) == num_kernel, "output_signal length (%d) should equal to num_kernel (%d)" % (len(output_signal), num_kernel)

    for i in range(num_kernel):
        assert np.mean(output_signal[i]) == 9 * (i+1), "Wrong convolution result! Expect %.2f but %.2f" % (np.mean(output_signal[i]), 11 * (i+1))

if __name__ == '__main__':
    
    test_maximum_voltage()
    test_passive_average()
    test_adder()
    test_subtractor()
    test_abs()
    test_v2v_conv()
