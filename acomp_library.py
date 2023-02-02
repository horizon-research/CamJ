import numpy as np
from utility import *


class PinnedPD(object):
    """docstring for pixel"""

    def __init__(self,
                 pd_capacitance=100e-15,
                 pd_supply=3.3
                 ):
        self.pd_capacitance = pd_capacitance
        self.pd_supply = pd_supply

    def pd_energy(self):
        energy = self.pd_capacitance * (self.pd_supply ** 2)
        return energy


class APS(PinnedPD):
    def __init__(self,
                 pd_capacitance,
                 pd_supply,
                 output_vs,
                 num_transistor=4,
                 fd_capacitance=10e-15,
                 num_readout=2,
                 load_capacitance=1e-12,
                 tech_node=130,
                 pitch=4,
                 array_vsize=128):
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

        energy_sf = (self.load_capacitance + get_pixel_parasitic(self.array_vsize, self.tech_node, self.pitch)) * \
                    self.pd_supply * self.output_vs
        energy_pd = super(APS, self).pd_energy()
        energy = energy_pd + energy_fd + self.num_readout * energy_sf
        return energy


class DPS(APS):
    def __init__(self,
                 pd_capacitance,
                 pd_supply,
                 output_vs,
                 num_transistor=4,
                 fd_capacitance=10e-15,
                 num_readout=2,
                 load_capacitance=1e-12,
                 tech_node=130,
                 pitch=4,
                 array_vsize=128,
                 ADC_FoM=100e-15,
                 ADC_reso=8,
                 ):
        super().__init__(pd_capacitance,
                         pd_supply,
                         output_vs,
                         num_transistor,
                         fd_capacitance,
                         num_readout,
                         load_capacitance,
                         tech_node,
                         pitch,
                         array_vsize)
        self.ADC_FoM = ADC_FoM
        self.ADC_reso = ADC_reso

    def energy(self):
        energy_aps = super(DPS, self).energy()
        energy_adc = ADC('SS', self.ADC_FoM, self.ADC_reso).energy()
        energy = energy_aps + energy_adc
        return energy


class PWM(PinnedPD):
    def __init__(self,
                 pd_capacitance,
                 pd_supply,
                 ramp_capacitance=1e-12,
                 gate_capacitance=10e-15,
                 num_readout=1):
        super().__init__(pd_capacitance, pd_supply)
        self.ramp_capacitance = ramp_capacitance
        self.num_readout = num_readout
        self.gate_capacitance = gate_capacitance

    def energy(self):
        energy_ramp = self.ramp_capacitance * (self.pd_supply ** 2)
        energy_comparator = self.gate_capacitance * (self.pd_supply ** 2)
        energy_pd = super(PWM, self).pd_energy()
        energy = energy_pd + self.num_readout * (energy_ramp + energy_comparator)
        return energy


########################################################################################################################
class AnalogMemory(object):
    """docstring for DataStorage"""

    def __init__(self,
                 type,
                 capacitance,
                 droop_rate,
                 t_sample,
                 t_hold,
                 supply,
                 resolution,
                 gain_opamp):
        self.type = type
        self.capacitance = capacitance
        self.droop_rate = droop_rate
        self.t_sample = t_sample
        self.t_hold = t_hold
        self.supply = supply
        self.resolution = resolution
        self.gain_opamp = gain_opamp

    def energy(self):
        if self.type == 'passive':
            energy = self.capacitance * (self.supply ** 2)
        if self.type == 'active':
            i_opamp = gm_id(load_capacitance=self.capacitance,
                            gain=np.where(self.gain_opamp is None,
                                          get_gain_min(resolution=self.resolution),
                                          self.gain_opamp),
                            bandwidth=1 / self.t_sample,
                            differential=True,
                            inversion_level='moderate')
            energy_opamp = self.supply * i_opamp * self.t_hold
            energy = energy_opamp + self.capacitance * (self.supply ** 2)
        return energy

    def delay(self):
        pass

    def stored_value(self,
                     input):
        output = input * (1 - self.t_hold * self.droop_rate)
        return output


########################################################################################################################
class dac_d_to_c(object):
    def __init__(self,
                 supply=1.8,
                 load_capacitance=2e-12,
                 t_readout=16e-6,
                 resolution=4,
                 i_dc):
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
    def __init__(self,
                 supply,
                 load_capacitance,
                 t_readout,
                 i_dc):
        self.supply = supply
        self.load_capacitance = load_capacitance
        self.t_readout = t_readout
        if i_dc is None:
            self.i_dc = self.load_capacitance * self.supply / self.t_readout
        else:
            self.i_dc = i_dc

    def energy(self):
        energy = self.supply * self.i_dc * self.t_readout


class Comparator(object):
    def __init__(self,
                 supply,
                 i_bias,
                 t_readout):
        self.supply = supply
        self.i_bias = i_bias
        self.t_readout = t_readout

    def energy(self):
        energy = self.supply * self.i_bias * self.t_readout
        return energy


class Passive_SC(object):
    def __init__(self,
                 capacitance_array,
                 vs_array):
        self.capacitance_array = capacitance_array
        self.vs_array = vs_array

    def energy(self):
        energy = np.sum(np.multiply(self.capacitance_array, self.vs_array ** 2))
        return energy


class max_v(object):
    # source: https://www.mdpi.com/1424-8220/20/11/3101
    def __init__(self,
                 supply,
                 t_frame,
                 t_acomp,
                 load_capacitance=1e-12,
                 gain=10):
        self.supply = supply
        self.load_capacitance = load_capacitance
        self.t_frame = t_frame
        self.t_acomp = t_acomp
        self.gain = gain

    def energy(self):
        i_bias = gm_id(self.load_capacitance, gain=self.gain, bandwidth=1 / self.t_acomp, differential=False,
                       inversion_level='strong')
        energy_bias = self.supply * (0.5 * i_bias) * self.t_frame
        energy_amplifier = self.supply * i_bias * self.t_acomp
        energy = energy_bias + energy_amplifier
        return energy


########################################################################################################################
class ADC(object):
    """docstring for differential-input rail-to-rail ADC"""

    def __init__(self,
                 type,
                 FOM,
                 resolution):
        self.type = type
        self.FOM = FOM
        self.resolution = resolution

    def energy(self):
        energy = self.FOM * (2 ** self.resolution)
        return energy

    def delay(self):
        pass

    def quantization_noise(self):  # [unit: V]
        LSB = self.supply_voltage / 2 ** (self.resolution - 1)
        return 1 / 12 * LSB ** 2

########################################################################################################################
