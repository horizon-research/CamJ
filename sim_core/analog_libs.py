import numpy as np

from sim_core.analog_perf_libs import ColumnAmplifierPerf, SourceFollowerPerf, SourceFollowerPerf,\
                                      ActiveAnalogMemoryPerf, PassiveAnalogMemoryPerf,\
                                      DigitalToCurrentConverterPerf, CurrentMirrorPerf,\
                                      ComparatorPerf
from functional_core.noise_model import ColumnwiseNoise, PixelwiseNoise, FloatingDiffusionNoise,\
                                        CurrentMirrorNoise, ComparatorNoise
                                        


class ColumnAmplifierPerf(object):
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
        load_capacitance=1e-12,  # [F]
        input_capacitance=1e-12,  # [F]
        t_sample=2e-6,  # [s]
        t_frame=10e-3,  # [s]
        supply=1.8,  # [V]
        gain=2,
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
            gain = gain
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

    def noise(self):
        pass

class SourceFollower(object):
    """
    NMOS-based constant current-biased source follower.
    """

    def __init__(
        self,
        # performance parameters
        load_capacitance=1e-12,  # [F]
        supply=1.8,  # [V]
        output_vs=1,  # [V]
        bias_current=5e-6,  # [A]
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
            gain = sf_gain,
            noise = sf_read_noise,
            enable_prnu = True,
            prnu_std = sf_prnu_std
        )

    def energy(self):
        return self.perf_model.energy()

    def noise(self):
        pass

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
        sample_capacitance=2e-12,  # [F]
        comp_capacitance=2.5e-12,  # [F]
        t_sample=1e-6,  # [s]
        t_hold=10e-3,  # [s]
        supply=1.8,  # [V]
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

    def noise(self):
        pass


class PassiveAnalogMemory(object):
    def __init__(
        self,
        # performance parameters
        capacitance=1e-12,  # [F]
        supply=1.8,  # [V]
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

    def noise(self):
        pass

class CurrentMirror(object):
    def __init__(
        self,
        # performance parameters
        supply=1.8,
        load_capacitance=2e-12,  # [F]
        t_readout=1e-6,  # [s]
        i_dc=1e-6,  # [A]
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

    def noise(self):
        pass

class PassiveSwitchedCapacitorArrayPerf(object):
    def __init__(
        self,
        capacitance_array,
        vs_array
    ):
        self.capacitance_array = capacitance_array
        self.vs_array = vs_array

    def energy(self):
        energy = np.sum(np.multiply(self.capacitance_array, self.vs_array ** 2))
        return energy


class Comparator(object):
    def __init__(
        self,
        # performance parameters
        supply=1.8,  # [V]
        i_bias=10e-6,  # [A]
        t_readout=1e-9,  # [s]
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

    def noise(self):
        pass

























