import numpy as np
import time

from camj.sim_core.analog_perf_libs import ColumnAmplifierPerf, SourceFollowerPerf, SourceFollowerPerf,\
                                      ActiveAnalogMemoryPerf, PassiveAnalogMemoryPerf,\
                                      DigitalToCurrentConverterPerf, CurrentMirrorPerf,\
                                      ComparatorPerf, PassiveSwitchedCapacitorArrayPerf,\
                                      AnalogToDigitalConverterPerf, DigitalToCurrentConverterPerf,\
                                      MaximumVoltagePerf, GeneralCircuitPerf
from camj.functional_core.noise_model import ColumnwiseNoise, PixelwiseNoise, FloatingDiffusionNoise,\
                                        CurrentMirrorNoise, ComparatorNoise,\
                                        PassiveSwitchedCapacitorArrayNoise, AnalogToDigitalConverterNoise,\
                                        AbsoluteDifferenceNoise, MaximumVoltageNoise

class ColumnAmplifier(object):
    """
    NMOS-based single-input-single-output cascode amplifier.

    @article{capoccia2019experimental,
      title={Experimental verification of the impact of analog CMS on CIS readout noise},
      author={Capoccia, Raffaele and Boukhayma, Assim and Enz, Christian},
      journal={IEEE Transactions on Circuits and Systems I: Regular Papers},
      volume={67},
      number={3},
      pages={774--784},
      year={2019},
      publisher={IEEE}
    }
    """

    def __init__(
        self,
        # performance parameters
        load_capacitance = 1e-12,  # [F]
        input_capacitance = 1e-12,  # [F]
        t_sample = 2e-6,  # [s]
        t_frame = 10e-3,  # [s]
        supply = 1.8,  # [V]
        gain = 2,
        gain_open = 256,
        differential = False,
        # noise parameters
        noise = 0.,
        enable_prnu = False,
        prnu_std = 0.001,
        enable_offset = False,
        pixel_offset_voltage = 0.1,
        col_offset_voltage = 0.05
    ):
        self.perf_model = ColumnAmplifierPerf(
            load_capacitance = load_capacitance,
            input_capacitance = input_capacitance,
            t_sample = t_sample,
            t_frame = t_frame,
            supply = supply,
            gain = gain,
            gain_open = gain_open,
            differential = differential
        )

        self.noise_model = ColumnwiseNoise(
            name = "ColumnAmplifier",
            gain = gain,
            noise = noise,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std
        )

    def energy(self):
        return self.perf_model.energy()

    def noise(self, input_signal_list):
        output_signal_list = []
        for input_signal in input_signal_list:
            output_signal_list.append(
                self.noise_model.apply_gain_and_noise(
                    input_signal
                )
            )
        return (self.noise_model.name, output_signal_list)

class SourceFollower(object):
    """
    NMOS-based constant current-biased source follower.
    """

    def __init__(
        self,
        # performance parameters
        load_capacitance = 1e-12,  # [F]
        supply = 1.8,  # [V]
        output_vs = 1,  # [V]
        bias_current = 5e-6,  # [A]
        # noise parameters
        gain = 1.0,
        noise = 0.,
        enable_prnu = False,
        prnu_std = 0.001,
    ):
        self.perf_model = SourceFollowerPerf(
            load_capacitance = load_capacitance,
            supply = supply,
            output_vs = output_vs,
            bias_current = bias_current,
        )

        self.noise_model = PixelwiseNoise(
            name = "SourceFollower",
            gain = gain,
            noise = noise,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std
        )

    def energy(self):
        return self.perf_model.energy()

    def noise(self, input_signal_list):
        output_signal_list = []
        for input_signal in input_signal_list:
            output_signal_list.append(
                self.noise_model.apply_gain_and_noise(
                    input_signal
                )
            )
        return (self.noise_model.name, output_signal_list)

class ActiveAnalogMemory(object):
    """
    PMOS-based differential-input-single-output amplifier.

    @article{o200410,
    title={A 10-nW 12-bit accurate analog storage cell with 10-aA leakage},
    author={O'Halloran, Micah and Sarpeshkar, Rahul},
    journal={IEEE journal of solid-state circuits},
    volume={39},
    number={11},
    pages={1985--1996},
    year={2004},
    publisher={IEEE}
    }
    """

    def __init__(
        self,
        # performance parameters
        sample_capacitance = 2e-12,  # [F]
        comp_capacitance = 2.5e-12,  # [F]
        t_sample = 1e-6,  # [s]
        t_hold = 10e-3,  # [s]
        supply = 1.8,  # [V]
        # eqv_reso,# equivalent resolution
        # opamp_dcgain
        # noise parameters
        gain = 1.0,
        noise = 0.,
        enable_prnu = False,
        prnu_std = 0.001,
    ):
        self.perf_model = ActiveAnalogMemoryPerf(
            sample_capacitance = sample_capacitance,
            comp_capacitance = comp_capacitance,
            t_sample = t_sample,
            t_hold = t_hold,
            supply = supply
        )

        self.noise_model = PixelwiseNoise(
            name = "ActiveAnalogMemory",
            gain = gain,
            noise = noise,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std
        )

    def energy(self):
        return self.perf_model.energy() 

    def noise(self, input_signal_list):
        output_signal_list = []
        for input_signal in input_signal_list:
            output_signal_list.append(
                self.noise_model.apply_gain_and_noise(
                    input_signal
                )
            )
        return (self.noise_model.name, output_signal_list)


class PassiveAnalogMemory(object):
    def __init__(
        self,
        # performance parameters
        capacitance = 1e-12,  # [F]
        supply = 1.8,  # [V]
        # eqv_reso  # equivalent resolution
        # noise parameters
        gain = 1.0,
        noise = 0.,
        enable_prnu = False,
        prnu_std = 0.001,
    ):
        self.perf_model = PassiveAnalogMemoryPerf(
            capacitance = capacitance,
            supply = supply
        )

        self.noise_model = PixelwiseNoise(
            name = "PassiveAnalogMemory",
            gain = gain,
            noise = noise,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std
        )

    def energy(self):
        return self.perf_model.energy()

    def noise(self, input_signal_list):
        output_signal_list = []
        for input_signal in input_signal_list:
            output_signal_list.append(
                self.noise_model.apply_gain_and_noise(
                    input_signal
                )
            )
        return (self.noise_model.name, output_signal_list)

class CurrentMirror(object):
    def __init__(
        self,
        # performance parameters
        supply = 1.8,
        load_capacitance = 2e-12,  # [F]
        t_readout = 1e-6,  # [s]
        i_dc = 1e-6,  # [A]
        # noise parameters
        gain = 1.0,
        noise = 0.,
        enable_compute = False,
        enable_prnu = False,
        prnu_std = 0.001

    ):
        self.perf_model = CurrentMirrorPerf(
            supply = supply,
            load_capacitance = load_capacitance,
            t_readout = t_readout,
            i_dc = i_dc
        )

        self.noise_model = CurrentMirrorNoise(
            name = "CurrentMirror",
            gain = gain,
            noise = noise,
            enable_compute = enable_compute,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std
        )

    def energy(self):
        return self.perf_model.energy()

    def noise(self, input_signal_list):
        if len(input_signal_list) == 2:
            return (
                self.noise_model.name, 
                [self.noise_model.apply_gain_and_noise(input_signal_list[0], input_signal_list[1])]
            )
        elif len(input_signal_list) == 1:
            return (
                self.noise_model.name, 
                [self.noise_model.apply_gain_and_noise(input_signal_list[0])]
            )
        else:
            raise Exception("Input signal list to CurrentMirror can only be length of 1 or 2!")


class PassiveSwitchedCapacitorArray(object):
    def __init__(
        self,
        # peformance parameters
        capacitance_array,
        vs_array,
        # noise parameters
        noise = 0.,
    ):
        self.perf_model = PassiveSwitchedCapacitorArrayPerf(
            capacitance_array = capacitance_array,
            vs_array = vs_array
        )

        self.noise_model = PassiveSwitchedCapacitorArrayNoise(
            name = "PassiveSwitchedCapacitorArray",
            num_capacitor = len(capacitance_array),
            noise = noise
        )

    def energy(self):
        return self.perf_model.energy()

    def noise(self):
        return (
            self.noise_model.name, 
            [self.noise_model.apply_gain_and_noise(input_signal_list)]
        )

class Comparator(object):
    def __init__(
        self,
        # performance parameters
        supply = 1.8,  # [V]
        i_bias = 10e-6,  # [A]
        t_readout = 1e-9,  # [s]
        # noise parameters
        gain = 1.0,
        noise = 0.,
        enable_prnu = False,
        prnu_std = 0.001
    ):
        self.perf_model = ComparatorPerf(
            supply = supply,
            i_bias = i_bias,
            t_readout = t_readout
        )

        self.noise_model = ComparatorNoise(
            name = "Comparator",
            gain = 1,
            noise = 0,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std
        )

    def energy(self):
        return self.perf_model.energy()

    def noise(self, input_signal_list):
        if len(input_signal_list) == 2:
            return (
                self.noise_model.name, 
                [self.noise_model.apply_gain_and_noise(input_signal_list[0], input_signal_list[1])]
            )
        else:
            raise Exception("Input signal list to Comparator can only be length of 2!")


class AnalogToDigitalConverter(object):
    """docstring for differential-input rail-to-rail ADC"""

    def __init__(
        self,
        # performance parameters
        supply=1.8,  # [V]
        type='SS',
        fom=100e-15,  # [J/conversion]
        resolution=8,
        # noise parameters
        adc_noise = 0.,
    ):
        self.perf_model = AnalogToDigitalConverterPerf(
            supply = supply,
            type = type,
            fom = fom,
            resolution = resolution,
        )

        self.noise_model = AnalogToDigitalConverterNoise(
            name = "AnalogToDigitalConverter",
            adc_noise = adc_noise,
            max_val = supply
        )

    def energy(self):
        return self.perf_model.energy()

    def noise(self, input_signal_list):
        output_signal_list = []
        for input_signal in input_signal_list:
            output_signal_list.append(
                self.noise_model.apply_gain_and_noise(
                    input_signal
                )
            )
        return (self.noise_model.name, output_signal_list)


class DigitalToCurrentConverter(object):
    def __init__(
        self,
        # performance parameters
        supply=1.8,  # [V]
        load_capacitance=2e-12,  # [F]
        t_readout=16e-6,  # [s]
        resolution=4,
        i_dc=None,  # [A]
        # noise parameters
        gain = 1.0,
        noise = 0.,
        enable_prnu = False,
        prnu_std = 0.001,
    ):
        self.perf_model = DigitalToCurrentConverterPerf(
            supply = supply,
            load_capacitance = load_capacitance,
            t_readout = t_readout,
            resolution = resolution,
            i_dc = i_dc
        )

        self.noise_model = PixelwiseNoise(
            name = "DigitalToCurrentConverter",
            gain = gain,
            noise = noise,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std
        )

    def energy(self):
        return self.perf_model.energy()

    def noise(self, input_signal_list):
        output_signal_list = []
        for input_signal in input_signal_list:
            output_signal_list.append(
                self.noise_model.apply_gain_and_noise(
                    input_signal
                )
            )
        return (self.noise_model.name, output_signal_list)


class MaximumVoltage(object):
    """docstring for MaximumVoltage"""
    def __init__(
        self, 
        supply = 1.8,  # [V]
        t_frame = 30e-3,  # [s]
        t_acomp = 1e-6,  # [s]
        load_capacitance = 1e-12,  # [F]
        gain = 10,
        # noise parameters
        noise = 0.0,
    ):
        super(MaximumVoltage, self).__init__()

        self.perf_model = MaximumVoltagePerf(
            supply = supply,  # [V]
            t_frame = t_frame,  # [s]
            t_acomp = t_acomp,  # [s]
            load_capacitance = load_capacitance,  # [F]
            gain = gain
        )

        self.noise_model = MaximumVoltageNoise(
            name = "MaximumVoltage",
            noise = noise
        )
        
    def energy(self):
        return self.perf_model.energy()

    def noise(self, input_signal_list):
        return (
                self.noise_model.name, 
                [self.noise_model.apply_gain_and_noise(input_signal_list)]
            )


class GeneralCircuit(object):
    """docstring for MaximumVoltage"""
    def __init__(
        self, 
        supply = 1.8,  # [V]
        t_operation = 30e-3,  # [s]
        i_dc = 1e-6,  # [s]
    ):
    
        self.perf_model = GeneralCircuitPerf(
            supply = supply,  # [V]
            i_dc = i_dc,  # [A]
            t_operation = t_operation  # [s]
        )
        
    def energy(self):
        return self.perf_model.energy()

    def noise(self, input_signal_list):
        raise Exception("noise function in MaximumVoltage has not been implemented yet!")

class Adder(object):
    def __init__(
        self,
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
    ):
        self.perf_model = ColumnAmplifierPerf(
            load_capacitance = load_capacitance,
            input_capacitance = input_capacitance,
            t_sample = t_sample,
            t_frame = t_frame,
            supply = supply,
            gain = 1.0,    # adder no need to amplify the signal
            gain_open = gain_open,
            differential = differential
        )

        if columnwise_op:
            self.noise_model = ColumnwiseNoise(
                name = "ColumnAmplifier",
                gain = 1.0,    # adder no need to amplify the signal
                noise = noise,
                enable_prnu = enable_prnu,
                prnu_std = prnu_std
            )
        else:
            self.noise_model = PixelwiseNoise(
                name = "Amplifier",
                gain = 1.0,    # adder no need to amplify the signal
                noise = noise,
                enable_prnu = enable_prnu,
                prnu_std = prnu_std
            )

    def energy(self):
        # here multiply by 2, because two input signal go through column amplifier
        return self.perf_model.energy() * 2 

    def noise(self, input_signal_list):
        if len(input_signal_list) == 2:
            noise_input1 = self.noise_model.apply_gain_and_noise(input_signal_list[0])
            noise_input2 = self.noise_model.apply_gain_and_noise(input_signal_list[1])
            return (
                "Adder", 
                [noise_input1 + noise_input2]
            )
        else:
            raise Exception("Input signal list to Comparator can only be length of 2!")


class Subtractor(object):
    def __init__(
        self,
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
    ):
        self.perf_model = ColumnAmplifierPerf(
            load_capacitance = load_capacitance,
            input_capacitance = input_capacitance,
            t_sample = t_sample,
            t_frame = t_frame,
            supply = supply,
            gain = 1.0,    # adder no need to amplify the signal
            gain_open = gain_open,
            differential = differential
        )

        if columnwise_op:
            self.noise_model = ColumnwiseNoise(
                name = "ColumnAmplifier",
                gain = 1.0,    # adder no need to amplify the signal
                noise = noise,
                enable_prnu = enable_prnu,
                prnu_std = prnu_std
            )
        else:
            self.noise_model = PixelwiseNoise(
                name = "Amplifier",
                gain = 1.0,    # adder no need to amplify the signal
                noise = noise,
                enable_prnu = enable_prnu,
                prnu_std = prnu_std
            )

    def energy(self):
        # here multiply by 2, because two input signal go through column amplifier
        return self.perf_model.energy() * 2 

    def noise(self, input_signal_list):
        if len(input_signal_list) == 2:
            noise_input1 = self.noise_model.apply_gain_and_noise(input_signal_list[0])
            noise_input2 = self.noise_model.apply_gain_and_noise(input_signal_list[1])
            return (
                "Subtractor", 
                [noise_input1 - noise_input2]
            )
        else:
            raise Exception("Input signal list to Comparator can only be length of 2!")


class AbsoluteDifference(object):
    def __init__(
        self,
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
    ):
        self.perf_model = ColumnAmplifierPerf(
            load_capacitance = load_capacitance,
            input_capacitance = input_capacitance,
            t_sample = t_sample,
            t_frame = t_frame,
            supply = supply,
            gain = 1.0,    # adder no need to amplify the signal
            gain_open = gain_open,
            differential = differential
        )

        
        self.noise_model = AbsoluteDifferenceNoise(
            name = "AbsoluteDifference",
            gain = 1.0,    # adder no need to amplify the signal
            noise = noise,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std
        )

    def energy(self):
        # here multiply by 2, because two input signal go through column amplifier
        return self.perf_model.energy() * 2 

    def noise(self, input_signal_list):
        if len(input_signal_list) == 2:
            return (
                self.noise_model.name, 
                [   
                    self.noise_model.apply_gain_and_noise(
                        input_signal_list[0], 
                        input_signal_list[1]
                    )
                ]
            )
        else:
            raise Exception("Input signal list to Comparator can only be length of 2!")

class PassiveAverage(object):
    def __init__(
        self,
        # peformance parameters
        capacitance_array,
        vs_array,
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
        
    ):
        self.psca_perf_model = PassiveSwitchedCapacitorArrayPerf(
            capacitance_array = capacitance_array,
            vs_array = vs_array
        )

        self.sf_perf_model = SourceFollowerPerf(
            load_capacitance = sf_load_capacitance,
            supply = sf_supply,
            output_vs = sf_output_vs,
            bias_current = sf_bias_current,
        )

        self.psca_noise_model = PassiveSwitchedCapacitorArrayNoise(
            name = "PassiveSwitchedCapacitorArray",
            num_capacitor = len(capacitance_array),
            noise = psca_noise
        )

        self.sf_noise_model = PixelwiseNoise(
            name = "SourceFollower",
            gain = sf_gain,
            noise = sf_noise,
            enable_prnu = sf_enable_prnu,
            prnu_std = sf_prnu_std
        )

    def energy(self):
        return self.psca_perf_model.energy() + self.sf_perf_model.energy()

    def noise(self, input_signal_list):
        return (
            "PassiveAverage", 
            [
                self.sf_noise_model.apply_gain_and_noise(
                    self.psca_noise_model.apply_gain_and_noise(
                        input_signal_list
                    )                
                )
            ]
        )

class PassiveBinning(object):
    def __init__(
        self,
        # peformance parameters
        capacitance_array,
        vs_array,
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
        
    ):

        self.kernel_size = None
        self.psca_perf_model = PassiveSwitchedCapacitorArrayPerf(
            capacitance_array = capacitance_array,
            vs_array = vs_array
        )

        self.sf_perf_model = SourceFollowerPerf(
            load_capacitance = sf_load_capacitance,
            supply = sf_supply,
            output_vs = sf_output_vs,
            bias_current = sf_bias_current,
        )

        self.psca_noise_model = PassiveSwitchedCapacitorArrayNoise(
            name = "PassiveSwitchedCapacitorArray",
            num_capacitor = len(capacitance_array),
            noise = psca_noise
        )

        self.sf_noise_model = PixelwiseNoise(
            name = "SourceFollower",
            gain = sf_gain,
            noise = sf_noise,
            enable_prnu = sf_enable_prnu,
            prnu_std = sf_prnu_std
        )

    def set_binning_config(self, kernel_size):
        if len(kernel_size) != 1:
            raise Exception("The length of kernel_size, num_kernels and stride should be 1.")

        if kernel_size[0][-1] != 1:
            raise Exception("'PassiveBinning' only support kernel channel size of 1.")

        self.kernel_size = kernel_size[0][:2]

    def energy(self):
        return self.psca_perf_model.energy() + self.sf_perf_model.energy()

    def noise(self, input_signal_list):
        output_signal_list = []
        for input_signal in input_signal_list:
            input_shape = input_signal.shape
            if len(input_shape) != 3:
                raise Exception("'PassiveBinning' only support 3D input.")
            new_input_shape = (
                input_shape[0] // self.kernel_size[0],
                self.kernel_size[0],
                input_shape[1] // self.kernel_size[1],
                self.kernel_size[1],
                input_shape[2]
            )
            transposed_input_signal = np.transpose(
                input_signal.reshape(new_input_shape), 
                (0, 2, 1, 3, 4)
            ).reshape(
                (
                    new_input_shape[0],
                    new_input_shape[2],
                    new_input_shape[1] * new_input_shape[3],
                    new_input_shape[4]
                )
            )

            psca_input_list = []
            for i in range(new_input_shape[1] * new_input_shape[3]):
                psca_input_list.append(
                    transposed_input_signal[:, :, i, :]
                )

            output_signal_list.append(
                self.sf_noise_model.apply_gain_and_noise(
                    self.psca_noise_model.apply_gain_and_noise(
                        psca_input_list
                    )
                )
            )
        return ("PassiveBinning", output_signal_list)


class ActiveAverage(object):
    def __init__(
        self,
        # performance parameters
        load_capacitance = 1e-12,  # [F]
        input_capacitance = 1e-12,  # [F]
        t_sample = 2e-6,  # [s]
        t_frame = 10e-3,  # [s]
        supply = 1.8,  # [V]
        gain = 1,
        gain_open = 256,
        differential = False,
        # noise parameters
        noise = 0.,
        enable_prnu = False,
        prnu_std = 0.001,
        enable_offset = False,
        pixel_offset_voltage = 0.1,
        col_offset_voltage = 0.05
    ):
        self.perf_model = ColumnAmplifierPerf(
            load_capacitance = load_capacitance,
            input_capacitance = input_capacitance,
            t_sample = t_sample,
            t_frame = t_frame,
            supply = supply,
            gain = gain,
            gain_open = gain_open,
            differential = differential
        )

        self.noise_model = ColumnwiseNoise(
            name = "ColumnAmplifier",
            gain = gain,
            noise = noise,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std
        )

    def set_binning_config(self, kernel_size):
        if len(kernel_size) != 1:
            raise Exception("The length of kernel_size, num_kernels and stride should be 1.")

        if kernel_size[0][-1] != 1:
            raise Exception("'PassiveBinning' only support kernel channel size of 1.")

        self.kernel_size = kernel_size[0][:2]

    def energy(self):
        return self.perf_model.energy() * self.kernel_size[0] * self.kernel_size[1]

    def noise(self, input_signal_list):
        output_signal_list = []
        for input_signal in input_signal_list:
            output_signal_list.append(
                self.noise_model.apply_gain_and_noise(
                    input_signal
                )
            )

        output_signal_sum = np.zeros(output_signal_list[0].shape)
        for output_signal in output_signal_list:
            output_signal_sum += output_signal

        return ["ActiveAverage", output_signal_sum / len(output_signal_list)]


class ActiveBinning(object):
    def __init__(
        self,
        # performance parameters
        load_capacitance = 1e-12,  # [F]
        input_capacitance = 1e-12,  # [F]
        t_sample = 2e-6,  # [s]
        t_frame = 10e-3,  # [s]
        supply = 1.8,  # [V]
        gain = 2,
        gain_open = 256,
        differential = False,
        # noise parameters
        noise = 0.,
        enable_prnu = False,
        prnu_std = 0.001,
        enable_offset = False,
        pixel_offset_voltage = 0.1,
        col_offset_voltage = 0.05
    ):
        self.perf_model = ColumnAmplifierPerf(
            load_capacitance = load_capacitance,
            input_capacitance = input_capacitance,
            t_sample = t_sample,
            t_frame = t_frame,
            supply = supply,
            gain = gain,
            gain_open = gain_open,
            differential = differential
        )

        self.noise_model = ColumnwiseNoise(
            name = "ColumnAmplifier",
            gain = gain,
            noise = noise,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std
        )

    def set_binning_config(self, kernel_size):
        if len(kernel_size) != 1:
            raise Exception("The length of kernel_size, num_kernels and stride should be 1.")

        if kernel_size[0][-1] != 1:
            raise Exception("'PassiveBinning' only support kernel channel size of 1.")

        self.kernel_size = kernel_size[0][:2]

    def energy(self):
        return self.perf_model.energy() * self.kernel_size[0] * self.kernel_size[1]

    def noise(self, input_signal_list):
        output_signal_list = []
        for input_signal in input_signal_list:
            input_shape = input_signal.shape
            if len(input_shape) != 3:
                raise Exception("'ActiveBinning' only support 3D input.")
            new_input_shape = (
                input_shape[0] // self.kernel_size[0],
                self.kernel_size[0],
                input_shape[1] // self.kernel_size[1],
                self.kernel_size[1],
                input_shape[2]
            )
            transposed_input_signal = np.transpose(
                input_signal.reshape(new_input_shape), 
                (0, 2, 1, 3, 4)
            ).reshape(
                (
                    new_input_shape[0],
                    new_input_shape[2],
                    new_input_shape[1] * new_input_shape[3],
                    new_input_shape[4]
                )
            )

            signal_after_colamp_list = []
            for i in range(new_input_shape[1] * new_input_shape[3]):
                signal_after_colamp_list.append(
                    self.noise_model.apply_gain_and_noise(
                        transposed_input_signal[:, :, i, :]
                    )
                )

            signal_sum = np.zeros(signal_after_colamp_list[0].shape)
            for signal_after_colamp in signal_after_colamp_list:
                signal_sum += signal_after_colamp

            output_signal_list.append(signal_sum / len(signal_after_colamp_list))

        return ("ActiveBinning", output_signal_list)


class Voltage2VoltageConv(object):
    def __init__(
        self,
        # peformance parameters
        capacitance_array,
        vs_array,
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
        
    ):
        if len(capacitance_array) != len(vs_array):
            raise Exception(
                "The length of 'capacitance_array' (%d) and the length of 'vs_array' (%d) should be the same!"\
                % (len(capacitance_array), len(vs_array))
            )

        self.kernel_size = None
        self.num_kernels = None
        self.stride = None
        self.len_capacitance_array = len(capacitance_array)
        self.psca_perf_model = PassiveSwitchedCapacitorArrayPerf(
            capacitance_array = capacitance_array,
            vs_array = vs_array
        )

        self.sf_perf_model = SourceFollowerPerf(
            load_capacitance = sf_load_capacitance,
            supply = sf_supply,
            output_vs = sf_output_vs,
            bias_current = sf_bias_current,
        )

        # initialize random number generator
        self.psca_noise = psca_noise
        random_seed = int(time.time())
        self.rs = np.random.RandomState(random_seed)

        self.sf_noise_model = PixelwiseNoise(
            name = "SourceFollower",
            gain = sf_gain,
            noise = sf_noise,
            enable_prnu = sf_enable_prnu,
            prnu_std = sf_prnu_std
        )

    def energy(self):
        return self.psca_perf_model.energy() + self.sf_perf_model.energy()

    def set_conv_config(self, kernel_size, num_kernels, stride):
        if len(kernel_size) != 1 or len(num_kernels) != 1 or len(stride) != 1:
            raise Exception("The length of kernel_size, num_kernels and stride should be 1.")

        if kernel_size[0][-1] != 1:
            raise Exception("'Voltage2VoltageConv' only support kernel channel size of 1.")

        self.kernel_size = kernel_size[0][:2]
        self.num_kernels = num_kernels[0]
        self.stride = stride[0][:2]

        if self.len_capacitance_array != self.kernel_size[0] * self.kernel_size[1]:
            raise Exception(
                "The length of capacitance_array (%d) doesn't match with kernel_size (%dx%d). "\
                 % (self.len_capacitance_array, self.kernel_size[0], self.kernel_size[1]))


    def single_channel_convolution(self, input_signal, weight_signal):
        in_height, in_width = input_signal.shape    # Input shape
        w_height, w_width = weight_signal.shape     # weight shape
        s_height, s_width = self.stride             # stride shape
        out_height = (in_height - (w_height - s_height)) // s_height
        out_width = (in_width - (w_width - s_width)) // s_width
        # initialize output
        output_signal = np.zeros((out_height, out_width))

        for r in range(out_height):
            for c in range(out_width):
                # find the corresponding input elements for output
                input_elements = input_signal[
                    r*s_height : r*s_height+w_height,
                    c*s_width : c*s_width+w_width
                ]
                output_signal[r, c] = np.sum(input_elements * weight_signal)

        return output_signal

    def noise(self, input_signal_list):

        if len(input_signal_list) != 2:
            raise Exception("Input to Voltage2VoltageConv limits to 2 (input+weight)!")

        image_input = None
        kernel_input = None
        for input_signal in input_signal_list:
            if input_signal.shape[:2] == self.kernel_size[:2]:
                kernel_input = input_signal
            else:
                image_input = input_signal

        if image_input is None:
            raise Exception("Input signal to 'Voltage2VoltageConv' has not been initialized.")
        if kernel_input is None or kernel_input.shape[-1] != self.num_kernels:
            raise Exception(
                "Number of Kernel in input signal doesn't match the num_kernels (%d)"\
                % self.num_kernels
            )

        conv_result_list = []
        for i in range(self.num_kernels):
            conv_result = self.single_channel_convolution(image_input, kernel_input[:, :, i])
            output_height, output_width = conv_result.shape

            conv_result_after_noise = self.rs.normal(
                scale = self.psca_noise,
                size = (output_height, output_width)
            ) + conv_result

            conv_result_list.append(
                self.sf_noise_model.apply_gain_and_noise(
                    conv_result_after_noise
                )
            )

        output_height, output_width = conv_result_list[0].shape
        output_result = np.zeros((output_height, output_width, self.num_kernels))

        for i in range(self.num_kernels):
            output_result[:, :, i] = conv_result_list[i]

        return ("Voltage2VoltageConv", [output_result])



class Time2VoltageConv(object):
    def __init__(
        self,
        # performance parameters for current mirror
        cm_supply = 1.8,
        cm_load_capacitance = 2e-12,  # [F]
        cm_t_readout = 1e-6,  # [s]
        cm_i_dc = 1e-6,  # [A]
        # performance parameters for analog memory
        am_capacitance = 1e-12,  # [F]
        am_supply = 1.8,  # [V]
        # eqv_reso  # equivalent resolution
        # noise parameters for current mirror
        cm_gain = 1.0,
        cm_noise = 0.,
        cm_enable_prnu = False,
        cm_prnu_std = 0.001,
        # noise parameters for analog memory
        am_gain = 1.0,
        am_noise = 0.,
        am_enable_prnu = False,
        am_prnu_std = 0.001,
        
    ):

        self.kernel_size = None
        self.num_kernels = None
        self.stride = None

        self.cm_perf_model = CurrentMirrorPerf(
            supply = cm_supply,
            load_capacitance = cm_load_capacitance,
            t_readout = cm_t_readout,
            i_dc = cm_i_dc
        )

        self.am_perf_model = PassiveAnalogMemoryPerf(
            capacitance = am_capacitance,
            supply = am_supply
        )

        self.cm_noise_model = CurrentMirrorNoise(
            name = "CurrentMirror",
            gain = cm_gain,
            noise = cm_noise,
            enable_compute = True,
            enable_prnu = cm_enable_prnu,
            prnu_std = cm_prnu_std
        )

        self.am_noise_model = PixelwiseNoise(
            name = "PassiveAnalogMemory",
            gain = am_gain,
            noise = am_noise,
            enable_prnu = am_enable_prnu,
            prnu_std = am_prnu_std
        )

    def energy(self):
        if self.kernel_size is None:
            raise Exception("'kernel_size' in 'Time2CurrentConv' hasn't been initialized.")

        mac_cnt = self.kernel_size[0] * self.kernel_size[1]
        return self.cm_perf_model.energy() * mac_cnt + self.am_perf_model.energy() * 2

    def set_conv_config(self, kernel_size, num_kernels, stride):
        if len(kernel_size) != 1 or len(num_kernels) != 1 or len(stride) != 1:
            raise Exception("The length of kernel_size, num_kernels and stride should be 1.")

        if kernel_size[0][-1] != 1:
            raise Exception("'Voltage2VoltageConv' only support kernel channel size of 1.")

        self.kernel_size = kernel_size[0][:2]
        self.num_kernels = num_kernels[0]
        self.stride = stride[0][:2]


    def single_channel_convolution(self, input_signal, weight_signal):
        in_height, in_width = input_signal.shape    # Input shape
        w_height, w_width = weight_signal.shape     # weight shape
        s_height, s_width = self.stride             # stride shape
        out_height = (in_height - (w_height - s_height)) // s_height
        out_width = (in_width - (w_width - s_width)) // s_width
        # initialize output
        output_signal = np.zeros((out_height, out_width))

        for r in range(out_height):
            for c in range(out_width):
                # find the corresponding input elements for output
                input_elements = input_signal[
                    r*s_height : r*s_height+w_height, 
                    c*s_width : c*s_width+w_width
                ]
                noise_output = self.cm_noise_model.apply_gain_and_noise(
                    input_signal = input_elements, 
                    weight_signal = weight_signal
                )
                output_signal[r, c] = np.sum(noise_output)

        return output_signal

    def noise(self, input_signal_list):
        if len(input_signal_list) != 2:
            raise Exception("Input to Voltage2VoltageConv limits to 2 (input+weight)!")

        image_input = None
        kernel_input = None
        for input_signal in input_signal_list:
            if input_signal.shape[:2] == self.kernel_size[:2]:
                kernel_input = input_signal
            else:
                image_input = input_signal

        if image_input is None:
            raise Exception("Input signal to 'Voltage2VoltageConv' has not been initialized.")

        if kernel_input is None or kernel_input.shape[-1] != self.num_kernels:
            raise Exception(
                "Number of Kernel in input signal doesn't match the num_kernels (%d)"\
                % self.num_kernels
            )

        conv_result_list = []
        for i in range(self.num_kernels):
            conv_result = self.single_channel_convolution(image_input, kernel_input[:, :, i])
            output_height, output_width = conv_result.shape
            conv_result_list.append(
                self.am_noise_model.apply_gain_and_noise(
                    conv_result
                )
            )

        output_height, output_width = conv_result_list[0].shape
        output_result = np.zeros((output_height, output_width, self.num_kernels))

        for i in range(self.num_kernels):
            output_result[:, :, i] = conv_result_list[i]

        return ("Time2CurrentConv", [output_result])


class AnalogReLU(object):
    def __init__(
        self,
        # performance parameters
        supply = 1.8,  # [V]
        i_bias = 10e-6,  # [A]
        t_readout = 1e-9,  # [s]
        # noise parameters
        gain = 1.0,
        noise = 0.,
        enable_prnu = False,
        prnu_std = 0.001
    ):
        self.name = "ReLU"
        self.perf_model = ComparatorPerf(
            supply = supply,
            i_bias = i_bias,
            t_readout = t_readout
        )

        self.noise_model = ComparatorNoise(
            name = "Comparator",
            gain = 1,
            noise = 0,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std
        )

    def energy(self):
        return self.perf_model.energy()

    def noise(self, input_signal_list):

        output_signal_list = []

        for input_signal in input_signal_list:
            zero_input_signal = np.zeros(input_signal.shape)
            output_signal_list.append(
                self.noise_model.apply_gain_and_noise(
                    input_signal1 = input_signal, 
                    input_signal2 = zero_input_signal
                )
            )

        return (self.name, output_signal_list)











