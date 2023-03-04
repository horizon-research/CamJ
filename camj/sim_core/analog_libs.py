import numpy as np

from camj.sim_core.analog_perf_libs import ColumnAmplifierPerf, SourceFollowerPerf, SourceFollowerPerf,\
                                      ActiveAnalogMemoryPerf, PassiveAnalogMemoryPerf,\
                                      DigitalToCurrentConverterPerf, CurrentMirrorPerf,\
                                      ComparatorPerf, PassiveSwitchedCapacitorArrayPerf,\
                                      AnalogToDigitalConverterPerf, DigitalToCurrentConverterPerf,\
                                      MaximumVoltagePerf, GeneralCircuitPerf
from camj.functional_core.noise_model import ColumnwiseNoise, PixelwiseNoise, FloatingDiffusionNoise,\
                                        CurrentMirrorNoise, ComparatorNoise,\
                                        PassiveSwitchedCapacitorArrayNoise, AnalogToDigitalConverterNoise

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
            name = "ColumnAmplifierNoise",
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
        return output_signal_list

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
        return output_signal_list

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
            name = "ActiveMemNoise",
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
        return output_signal_list


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
            name = "PasstiveMemNoise",
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
        return output_signal_list

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
            name = "CurrentMirrorNoise",
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
            return [self.noise_model.apply_gain_and_noise(input_signal_list[0], input_signal_list[1])]
        elif len(input_signal_list) == 1:
            return [self.noise_model.apply_gain_and_noise(input_signal_list[0])]
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
            name = "PassiveSCNoise",
            num_capacitor = len(capacitance_array),
            noise = noise
        )

    def energy(self):
        return self.perf_model.energy()

    def noise(self):
        return [self.noise_model.apply_gain_and_noise(input_signal_list)]

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
            name = "ComparatorNoise",
            gain = 1,
            noise = 0,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std
        )

    def energy(self):
        return self.perf_model.energy()

    def noise(self, input_signal_list):
        if len(input_signal_list) == 2:
            return [self.noise_model.apply_gain_and_noise(input_signal_list[0], input_signal_list[1])]
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
            name = "ADCnoise",
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
        return output_signal_list


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
            name = "PasstiveMemNoise",
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
        return output_signal_list


class MaximumVoltage(object):
    """docstring for MaximumVoltage"""
    def __init__(
        self, 
        supply = 1.8,  # [V]
        t_frame = 30e-3,  # [s]
        t_acomp = 1e-6,  # [s]
        load_capacitance = 1e-12,  # [F]
        gain = 10
    ):
        super(MaximumVoltage, self).__init__()

        self.perf_model = MaximumVoltagePerf(
            supply = supply,  # [V]
            t_frame = t_frame,  # [s]
            t_acomp = t_acomp,  # [s]
            load_capacitance = load_capacitance,  # [F]
            gain = gain
        )
        
    def energy(self):
        return self.perf_model.energy()

    def noise(self, input_signal_list):
        raise Exception("noise function in MaximumVoltage has not been implemented yet!")


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



















