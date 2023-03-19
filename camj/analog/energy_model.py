import numpy as np
from camj.analog.energy_utils import gm_id, get_pixel_parasitic, parallel_impedance, get_delay


class PinnedPhotodiodePerf(object):
    """docstring for pixel"""

    def __init__(self,
                 pd_capacitance=100e-15,  # [F]
                 pd_supply=3.3  # [V]
                 ):
        self.pd_capacitance = pd_capacitance
        self.pd_supply = pd_supply

    def energy(self):
        energy = self.pd_capacitance * (self.pd_supply ** 2)
        return energy


class ActivePixelSensorPerf(PinnedPhotodiodePerf):
    def __init__(
        self,
        pd_capacitance,
        pd_supply,
        dynamic_sf = False,
        output_vs = 1,  # output voltage swing [V]
        num_transistor = 4,
        fd_capacitance = 10e-15,  # [F]
        num_readout = 2,
        load_capacitance = 1e-12,  # [F]
        tech_node = 130,  # [um]
        pitch = 4,  # [um]
        array_vsize = 128
    ):
        super().__init__(pd_capacitance, pd_supply)
        self.dynamic_sf = dynamic_sf
        self.num_transistor = num_transistor
        self.num_readout = num_readout
        self.fd_capacitance = fd_capacitance
        self.load_capacitance = load_capacitance
        self.tech_node = tech_node
        self.pitch = pitch
        self.array_vsize = array_vsize
        if output_vs is None:
            self.output_vs = self.pd_supply - get_nominal_supply(self.tech_node)
        else:
            self.output_vs = output_vs

    def energy(self):
        if self.num_transistor == 3:
            energy_fd = 0
        elif self.num_transistor == 4:
            energy_fd = self.fd_capacitance * (self.pd_supply ** 2)
        else:
            raise Exception("Defined APS is not supported.")

        if self.dynamic_sf:
            energy_sf = (
                self.load_capacitance + 
                get_pixel_parasitic(self.array_vsize, self.tech_node, self.pitch)
            ) * self.output_vs**2
        else:
            energy_sf = (
                self.load_capacitance + 
                get_pixel_parasitic(self.array_vsize, self.tech_node, self.pitch)
            ) * self.pd_supply * self.output_vs

        energy_pd = super(ActivePixelSensorPerf, self).energy()
        energy = energy_pd + energy_fd + self.num_readout * energy_sf

        return energy

    def impedance(
        self,
        sf_bias_current=2e-6  # [A]
    ):
        input_impedance = None

        gm_id_ratio = 16
        gm_n = gm_id_ratio * sf_bias_current
        output_impedance = 1 / gm_n
        return [input_impedance, output_impedance]

    def capacitance(self):
        input_capacitance = None
        output_capacitance = self.load_capacitance
        return [input_capacitance, output_capacitance]


class DigitalPixelSensorPerf(ActivePixelSensorPerf):
    def __init__(
        self,
        pd_capacitance,
        pd_supply,
        dynamic_sf,
        output_vs,
        num_transistor,
        fd_capacitance,
        num_readout,
        load_capacitance,
        tech_node,
        pitch,
        array_vsize,
        adc_type='SS',
        adc_fom=100e-15,  # [J/conversion]
        adc_reso=8,
    ):
        super().__init__(
            pd_capacitance = pd_capacitance,
            pd_supply = pd_supply,
            output_vs = output_vs,
            num_transistor = num_transistor,
            fd_capacitance = fd_capacitance,
            num_readout = num_readout,
            load_capacitance = load_capacitance,
            tech_node = tech_node,
            pitch = pitch,
            array_vsize = array_vsize
        )
        self.adc_type = adc_type
        self.adc_fom = adc_fom
        self.adc_reso = adc_reso

    def energy(self):
        energy_aps = super(DigitalPixelSensorPerf, self).energy()
        energy_adc = AnalogToDigitalConverterPerf(self.pd_supply, self.adc_type, self.adc_fom, self.adc_reso).energy()
        energy = energy_aps + energy_adc
        
        return energy


class PulseWidthModulationPixelPerf(PinnedPhotodiodePerf):
    """
    @article{hsu20200,
    title={A 0.5-V real-time computational CMOS image sensor with programmable kernel for feature extraction},
    author={Hsu, Tzu-Hsiang and Chen, Yi-Ren and Liu, Ren-Shuo and Lo, Chung-Chuan and Tang, Kea-Tiong and Chang, Meng-Fan and Hsieh, Chih-Cheng},
    journal={IEEE Journal of Solid-State Circuits},
    volume={56},
    number={5},
    pages={1588--1596},
    year={2020},
    publisher={IEEE}
    }
    """

    def __init__(
        self,
        pd_capacitance,
        pd_supply,
        array_vsize,
        ramp_capacitance=1e-12,  # [F]
        gate_capacitance=10e-15,  # [F]
        num_readout=1
    ):
        super().__init__(pd_capacitance, pd_supply)
        self.ramp_capacitance = ramp_capacitance
        self.num_readout = num_readout
        self.gate_capacitance = gate_capacitance
        self.array_vsize = array_vsize

    def energy(self):
        energy_parasitics = self.array_vsize/3*10e-15*(self.pd_supply**2)

        energy_ramp = self.ramp_capacitance * (self.pd_supply ** 2)
        energy_comparator = self.gate_capacitance * (self.pd_supply ** 2)
        energy_pd = super(PulseWidthModulationPixelPerf, self).energy()
        energy = energy_pd + self.num_readout * (energy_ramp * 2 + energy_comparator + energy_parasitics)
        
        return energy


########################################################################################################################
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
        load_capacitance=1e-12,  # [F]
        input_capacitance=1e-12,  # [F]
        t_sample=2e-6,  # [s]
        t_frame=10e-3,  # [s]
        supply=1.8,  # [V]
        gain=2,
        gain_open=256,
        differential = False,
    ):
        self.load_capacitance = load_capacitance
        self.input_capacitance = input_capacitance
        self.t_sample = t_sample
        self.t_frame = t_frame
        self.supply = supply
        self.gain = gain
        self.gain_open = gain_open
        self.fb_capacitance = self.input_capacitance / self.gain
        [self.i_opamp, self.gm] = gm_id(
            load_capacitance=self.load_capacitance,
            gain=self.gain_open,
            bandwidth=1 / self.t_sample,
            differential=differential,
            inversion_level='moderate'
        )
        self.gd = self.gm / 100  # gd<<gm

    def energy(self):
        energy_opamp = self.supply * self.i_opamp * self.t_frame
        energy = energy_opamp + (self.input_capacitance + self.fb_capacitance + self.load_capacitance) \
                 * (self.supply ** 2)
        # print(self.i_opamp, energy_opamp)
        return energy

    def impedance(self):
        input_impedance = float('inf')

        gm_n = gm_p = self.gm
        gd_n = gd_p = self.gd
        output_impedance = parallel_impedance([gm_n * (1 / gd_n) ** 2, gm_p * (1 / gd_p) ** 2])
        return [input_impedance, output_impedance]

    def capacitance(self):
        input_capacitance = self.input_capacitance
        output_capacitance = self.load_capacitance
        return [input_capacitance, output_capacitance]


class SourceFollowerPerf(object):
    """
    NMOS-based constant current-biased source follower.
    """

    def __init__(
        self,
        load_capacitance=1e-12,  # [F]
        supply=1.8,  # [V]
        output_vs=1,  # [V]
        bias_current=5e-6  # [A]
    ):
        self.load_capacitance = load_capacitance
        self.supply = supply
        self.output_vs = output_vs
        self.bias_current = bias_current

    def energy(self):
        energy = self.load_capacitance * self.supply * self.output_vs
        return energy

    def impedance(self):
        input_impedance = float('inf')

        gm_id_ratio = 16
        gm_n = gm_id_ratio * self.bias_current
        output_impedance = 1 / gm_n
        return [input_impedance, output_impedance]

    def capacitance(self):
        input_capacitance = 0
        output_capacitance = self.load_capacitance
        return [input_capacitance, output_capacitance]


class ActiveAnalogMemoryPerf(object):
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
        sample_capacitance=2e-12,  # [F]
        comp_capacitance=2.5e-12,  # [F]
        t_sample=1e-6,  # [s]
        t_hold=10e-3,  # [s]
        supply=1.8,  # [V]
        # eqv_reso,# equivalent resolution
        # opamp_dcgain
    ):
        self.sample_capacitance = sample_capacitance
        self.comp_capacitance = comp_capacitance
        self.t_sample = t_sample
        self.t_hold = t_hold
        self.supply = supply
        # self.eqv_reso = eqv_reso
        # self.opamp_dcgain = opamp_dcgain
        [self.i_opamp, self.gm] = gm_id(
            load_capacitance=self.comp_capacitance,
            gain=300,
            bandwidth=1 / self.t_sample,
            differential=True,
            inversion_level='moderate'
        )
        self.gd = self.gm / 100

    def energy(self):
        energy_opamp = self.supply * self.i_opamp * self.t_hold
        energy = energy_opamp + (self.sample_capacitance + self.comp_capacitance) * (self.supply ** 2)
        return energy

    def impedance(self):
        input_impedance = float('inf')

        gm_n = gm_p = self.gm
        gd_n = gd_p = self.gd
        output_impedance = parallel_impedance([gm_n * (1 / gd_n) ** 2, gm_p * (1 / gd_p) ** 2])
        return [input_impedance, output_impedance]

    def capacitance(self):
        input_capacitance = self.sample_capacitance
        output_capacitance = self.comp_capacitance
        return [input_capacitance, output_capacitance]


class PassiveAnalogMemoryPerf(object):
    def __init__(
        self,
        capacitance=1e-12,  # [F]
        supply=1.8,  # [V]
        # eqv_reso  # equivalent resolution
    ):
        self.capacitance = capacitance
        self.supply = supply
        # self.eqv_reso = eqv_reso

    def energy(self):
        energy = self.capacitance * (self.supply ** 2)
        return energy

    def impedance(self):
        input_impedance = float('inf')
        output_impedance = float('inf')
        return [input_impedance, output_impedance]

    def capacitance(self):
        input_capacitance = self.capacitance
        output_capacitance = 0
        return [input_capacitance, output_capacitance]


########################################################################################################################
class DigitalToCurrentConverterPerf(object):
    def __init__(
        self,
        supply=1.8,  # [V]
        load_capacitance=2e-12,  # [F]
        t_readout=16e-6,  # [s]
        resolution=4,
        i_dc=None  # [A]
    ):
        self.supply = supply
        self.load_capacitance = load_capacitance
        self.t_readout = t_readout
        self.resolution = resolution  # aka num_current_path
        if i_dc is None:
            self.i_dc = self.load_capacitance * self.supply / self.t_readout
        else:
            self.i_dc = i_dc

    def energy(self):
        energy = self.supply * self.i_dc * self.t_readout * (2 ** self.resolution)
        return energy


class CurrentMirrorPerf(object):
    def __init__(
        self,
        supply=1.8,
        load_capacitance=2e-12,  # [F]
        t_readout=1e-6,  # [s]
        i_dc=1e-6  # [A]
    ):
        self.supply = supply
        self.load_capacitance = load_capacitance
        self.t_readout = t_readout
        if i_dc is None:
            self.i_dc = self.load_capacitance * self.supply / self.t_readout
        else:
            self.i_dc = i_dc

    def energy(self):
        return self.supply * self.i_dc * self.t_readout



class PassiveSwitchedCapacitorArrayPerf(object):
    def __init__(
        self,
        capacitance_array,
        vs_array
    ):
        self.capacitance_array = capacitance_array
        self.vs_array = vs_array

    def energy(self):
        energy = np.sum(np.multiply(self.capacitance_array, [vs ** 2 for vs in self.vs_array]))
        return energy


class MaximumVoltagePerf(object):
    # source: https://www.mdpi.com/1424-8220/20/11/3101
    def __init__(
        self,
        supply=1.8,  # [V]
        t_frame=30e-3,  # [s]
        t_acomp=1e-6,  # [s]
        load_capacitance=1e-12,  # [F]
        gain=10
    ):
        self.supply = supply
        self.load_capacitance = load_capacitance
        self.t_frame = t_frame
        self.t_acomp = t_acomp
        self.gain = gain

    def energy(self):
        i_bias, _ = gm_id(
            self.load_capacitance, 
            gain = self.gain, 
            bandwidth = 1 / self.t_acomp, 
            differential = True,
            inversion_level = 'moderate'
        )
        energy_bias = self.supply * (0.5 * i_bias) * self.t_frame
        energy_amplifier = self.supply * i_bias * self.t_acomp
        energy = energy_bias + energy_amplifier
        return energy


########################################################################################################################
class ComparatorPerf(object):
    def __init__(
        self,
        supply=1.8,  # [V]
        i_bias=10e-6,  # [A]
        t_readout=1e-9  # [s]
    ):
        self.supply = supply
        self.i_bias = i_bias
        self.t_readout = t_readout

    def energy(self):
        energy = self.supply * self.i_bias * self.t_readout
        return energy


class AnalogToDigitalConverterPerf(object):
    """docstring for differential-input rail-to-rail ADC"""

    def __init__(
        self,
        supply=1.8,  # [V]
        type='SS',
        fom=100e-15,  # [J/conversion]
        resolution=8,
    ):
        self.supply = supply
        self.type = type
        self.fom = fom
        self.resolution = resolution

    def energy(self):
        energy = self.fom * (2 ** self.resolution)
        return energy

    def delay(self):
        pass

    def quantization_noise(self):  # [unit: V]
        LSB = self.supply / 2 ** (self.resolution - 1)
        return 1 / 12 * LSB ** 2



class GeneralCircuitPerf(object):
    def __init__(
        self,
        supply=1.8,  # [V]
        i_dc=10e-6,  # [A]
        t_operation=1e-9  # [s]
    ):
        self.supply = supply
        self.i_dc = i_dc
        self.t_operation = t_operation

    def energy(self):
        energy = self.supply * self.i_dc * self.t_operation
        return energy


########################################################################################################################