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


class DPS(PinnedPD):
    def __init__(self):
        super().__init__()

    def energy(self):
        pass


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
                 supply,
                 load_capacitance,
                 t_readout,
                 resolution,
                 num_current_path):
        self.supply = supply
        self.load_capacitance = load_capacitance
        self.t_readout = t_readout
        self.resolution = resolution
        self.num_current_path = num_current_path

    def energy(self):
        i_max = self.load_capacitance * self.supply / self.t_readout
        energy = self.supply * i_max * self.t_readout * self.num_current_path
        return energy


class current_mirror(object):
    def __init__(self,
                 supply,
                 load_capacitance,
                 t_readout,
                 resolution):
        self.supply = supply
        self.load_capacitance = load_capacitance
        self.t_readout = t_readout
        self.resolution = resolution

    def energy(self):
        pass


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


########################################################################################################################
class ADC(object):
    """docstring for differential-input rail-to-rail ADC"""

    def __init__(self,
                 type,
                 FOM,
                 resolution,
                 sampling_rate):
        self.type = type
        self.FOM = FOM
        self.resolution = resolution
        self.sampling_rate = sampling_rate

    def energy(self):
        energy = self.FOM * (2 ** self.resolution)
        return energy

    def delay(self):
        pass

    def quantization_noise(self):  # [unit: V]
        LSB = self.supply_voltage / 2 ** (self.resolution - 1)
        return 1 / 12 * LSB ** 2

########################################################################################################################
