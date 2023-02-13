import numpy as np
from sim_core.analog_utils import *

# basic class PinnedPhotodiode
class PinnedPD(object):
    """
        This is the basic photodiode class.

        DO NOT USE THIS CLASS TO IMPLEMENT YOUR ANALOG CONFIGURATION.
    """

    def __init__(
        self,
        pd_capacitance=100e-15,  # [F]
        pd_supply=3.3  # [V]
    ):
        self.pd_capacitance = pd_capacitance
        self.pd_supply = pd_supply

    def energy(self):
        energy = self.pd_capacitance * (self.pd_supply ** 2)
        return energy

# Active pxiel sensor
class ActivePixelSensor(PinnedPD):
    """
        Pixel sensor analog enery model

        Our APS model includes modeling photodiode (PD), floating diffusion (FD), source follower (SF,
        and parasitic during the readout.

        Our APS model supports energy estimation for both 3T-APS and 4T-APS. Users need to define
        `num_transistor` to get the correct energy estimation.

        Input parameters:
            pd_capacitance: the capacitance of PD.
            pd_supply: supply voltage
            output_vs: output voltage swing, the typical value range is [?, ?].
            num_transistor: this parameters define 3T or 4T APS.
            num_readout: if enable CDS, then num_readout is 2 otherwise 1
            load_capacitance: load capacitance at the output of the pixel
            tech_node: the technology process node.
            pitch: pitch, pixel pitch size (width or height)
            array_vsize: pixel array vertical size, only use for rolling shutter. 
                         To estimate parasitic capacitance on vertical wire.
    """
    def __init__(
        self,
        pd_capacitance,
        pd_supply,
        output_vs,  # output voltage swing [V]
        num_transistor=4,
        fd_capacitance=10e-15,  # [F]
        num_readout=2,
        load_capacitance=1e-12,  # [F]
        tech_node=130,  # [um]
        pitch=4,  # [um]
        array_vsize=128
    ):
        super().__init__(pd_capacitance, pd_supply)
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
        if self.num_transistor == 4:
            energy_fd = self.fd_capacitance * (self.pd_supply ** 2)
        if self.num_transistor == 3:
            energy_fd = 0
        else:
            raise Exception("Defined APS is not supported.")

        energy_sf = (
            self.load_capacitance + 
            get_pixel_parasitic(self.array_vsize, self.tech_node, self.pitch)
        ) * self.pd_supply * self.output_vs
        energy_pd = super(ActivePixelSensor, self).energy()
        energy = energy_pd + energy_fd + self.num_readout * energy_sf
        return energy

# digital pixel sensor
# DigitalPixelSensor
class DigitalPixelSensor(ActivePixelSensor):
    """
        Digital Pixel Sensor

        This class models the energy consumption of digital pixel sensor (DPS).

        It is basically a wrapper function to include one APS and one ADC. That is the actual
        implementation of DPS.

        Input parameters:
            pd_capacitance: the capacitance of PD.
            pd_supply: TODO???
            output_vs: output voltage swing, the typical value range is [?, ?].
            num_transistor: this parameters define 3T or 4T APS.
            num_readout: ???
            load_capacitance: ???
            tech_node: the technology process node.
            pitch: pitch size??
            array_vsize: ????,
            adc_type: the actual ADC type. Please check ADC class for more details.
            adc_fom: ???
            adc_resolution: the resolution of ADC. typical value range is from XX to XX.
    """
    def __init__(
        self,
        pd_capacitance,
        pd_supply,
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
            pd_capacitance,
            pd_supply,
            output_vs,
            num_transistor,
            fd_capacitance,
            num_readout,
            load_capacitance,
            tech_node,
            pitch,
            array_vsize
        )
        self.adc_type = adc_type
        self.adc_fom = adc_fom
        self.adc_reso = adc_reso

    def energy(self):
        energy_aps = super(DigitalPixelSensor, self).energy()
        energy_adc = ActivePixelSensor(self.pd_supply, self.adc_type, self.adc_fom, self.adc_reso).energy()
        energy = energy_aps + energy_adc
        return energy

class PulseWidthModulationPixel(PinnedPD):
    """
        Pulse Width Modulation Pixel

        This class models pulse width modulation pixel

        Input:
            pd_capacitance: PD capacitance
            pd_supply: PD voltage supply
            ramp_capacitance: capacitance of ramp generator
            gate_capacitance: the gate capacitance of readout transistor
            num_readout: number of read from pixel, can only be 1 or 2.

    """
    def __init__(
        self,
        pd_capacitance,
        pd_supply,
        ramp_capacitance=1e-12,  # [F]
        gate_capacitance=10e-15,  # [F]
        num_readout=1
    ):
        super().__init__(pd_capacitance, pd_supply)
        self.ramp_capacitance = ramp_capacitance
        self.num_readout = num_readout
        self.gate_capacitance = gate_capacitance

    def energy(self):
        energy_ramp = self.ramp_capacitance * (self.pd_supply ** 2)
        energy_comparator = self.gate_capacitance * (self.pd_supply ** 2)
        energy_pd = super(PulseWidthModulationPixel, self).energy()
        energy = energy_pd + self.num_readout * (energy_ramp + energy_comparator)
        return energy


# column amplifier
class ColumnAmplifier(object):
    """
        Column Amplifier

        This class models column amplifier by assuming column amplification energy comes from two 
        sources:
            1. energy from actual amplifier
            2. energy from capacitance used for negative feedback

        Input:
            capacitance_load:
            capacitance_input:
            t_sample: sampling time of operation amplifier (opamp)
            t_frame: sensor frame time. we assume opamp is always turned on during the frame time.
            supply: voltage supply
            gain: the closed-loop gain from column amplifier

    """
    def __init__(
        self,
        capacitance_load=1e-12,  # [F]
        capacitance_input=1e-12,  # [F]
        t_sample=2e-6,  # [s]
        t_frame=10e-3,  # [s]
        supply=1.8,  # [V]
        gain=2
    ):
        self.capacitance_load = capacitance_load
        self.capacitance_input = capacitance_input
        self.t_sample = t_sample
        self.t_frame = t_frame
        self.supply = supply
        self.gain = gain
        self.capacitance_feedback = self.capacitance_input / self.gain

    def energy(self):
        i_opamp, _ = gm_id(load_capacitance=self.capacitance_feedback + self.capacitance_load,
                        gain=self.gain,
                        bandwidth=1 / self.t_sample,
                        differential=False,
                        inversion_level='moderate')
        
        energy_opamp = self.supply * i_opamp * self.t_frame
        energy = energy_opamp + (self.capacitance_input + self.capacitance_feedback + self.capacitance_load) \
                 * (self.supply ** 2)
        return energy

# active analog memory 
class ActiveAnalogMemory(object):
    """
        Active Analog Memory

        Input:
            capacitance:
            t_sample: 
            t_hold:
            supply: supply voltage
    """
    def __init__(
        self,
        capacitance=1e-12,  # [F]
        t_sample=1e-6,  # [s]
        t_hold=10e-3,  # [s]
        supply=1.8,  # [V]
        # eqv_reso,# equivalent resolution
        # opamp_dcgain
    ):
        self.capacitance = capacitance
        self.t_sample = t_sample
        self.t_hold = t_hold
        self.supply = supply
        # self.eqv_reso = eqv_reso
        # self.opamp_dcgain = opamp_dcgain

    def energy(self):
        i_opamp, _ = gm_id(
            load_capacitance=self.capacitance,
            gain=1,
            bandwidth=1 / self.t_sample,
            differential=True,
            inversion_level='moderate'
        )
        energy_opamp = self.supply * i_opamp * self.t_hold
        energy = energy_opamp + self.capacitance * (self.supply ** 2)
        return energy

    def delay(self):
        pass

# passive analog memory
class PassiveAnalogMemory(object):
    """
        Passive Analog Memory

    """
    def __init__(
        self,
        capacitance=1e-12,  # [F]
        t_sample=1e-6,  # [s]
        t_hold=10e-3,  # [s],
        supply=1.8,  # [V]
        # eqv_reso  # equivalent resolution
    ):
        self.capacitance = capacitance
        self.t_sample = t_sample
        self.t_hold = t_hold
        self.supply = supply
        # self.eqv_reso = eqv_reso

    def energy(self):
        energy = self.capacitance * (self.supply ** 2)
        return energy

    def delay(self):
        pass


########################################################################################################################

# digitalToCurrent convertor 
class dac_d_to_c(object):
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


class current_mirror(object):
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
        energy = self.supply * self.i_dc * self.t_readout

# passive switch capacitor
class passive_SC(object):
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

# maxValue
# how many inputs?
class max_v(object):
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
        i_bias, _ = gm_id(self.load_capacitance, gain=self.gain, bandwidth=1 / self.t_acomp, differential=False,
                       inversion_level='strong')
        energy_bias = self.supply * (0.5 * i_bias) * self.t_frame
        energy_amplifier = self.supply * i_bias * self.t_acomp
        energy = energy_bias + energy_amplifier
        return energy


########################################################################################################################
class Comparator(object):
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


class ADC(object):
    """docstring for differential-input rail-to-rail ADC"""

    def __init__(
        self,
        supply=1.8,  # [V]
        type='SS',
        fom=100e-15,  # [J/conversioin]
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

########################################################################################################################