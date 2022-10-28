import numpy as np
from utility import *


class PinnedPD(object):
    """docstring for pixel"""

    def __init__(self,
                 pd_capacitance=10e-12,
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
                 num_transistor,
                 fd_capacitance,
                 num_readout,
                 t_readout,
                 load_capacitance):
        super().__init__(pd_capacitance, pd_supply)
        self.num_transistor = num_transistor
        self.num_readout = num_readout
        self.fd_capacitance = fd_capacitance
        self.load_capacitance = load_capacitance
        self.t_readout = t_readout

    def energy(self):
        if self.num_transistor == 4:
            energy_fd = self.fd_capacitance * (self.pd_supply ** 2)
        if self.num_transistor == 3:
            energy_fd = 0

        i_sf = gm_id(load_capacitance=self.load_capacitance,
                     gain=1,
                     bandwidth=1 / self.t_readout,
                     differential=False,
                     inversion_level='moderate')
        energy_sf = self.pd_supply * i_sf * self.t_readout

        energy_pd = super(APS, self).pd_energy()
        energy = energy_pd + self.num_readout * (energy_fd + energy_sf)
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
                 ramp_capacitance,
                 gate_capacitance,
                 num_readout):
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
class DigitalStorage(object):
    """docstring for DataStorage"""

    def __init__(self,
                 cell_type,
                 size,
                 technology,
                 port_num,
                 port_type,
                 access_type,
                 access_num,
                 arrangement):
        self.cell_type = cell_type
        self.size = size
        self.technology = technology
        self.port_num = port_num
        self.port_type = port_type
        self.access_type = access_type
        self.access_num = access_num
        self.arrangement = arrangement

    def area(self):
        area_ = self.size * unit_area(self.cell_type, self.technology, self.port_num, self.port_type)
        return area_

    def energy(self):
        energy_ = 0
        if self.access_type == 'read':
            unit_read_energy_ = unit_energy(self.cell_type, self.technology, self.port_type)
            energy_ += unit_read_energy_ * self.access_num
        elif self.access_type == 'write':
            unit_write_energy_ = unit_energy(self.cell_type, self.technology, self.port_type)
            energy_ += unit_write_energy_ * self.access_num
        return energy_

    def delay(self):
        delay_ = 0
        if self.access_type == 'read':
            unit_read_delay_ = unit_delay(self.cell_type, self.technology, self.port_type)
            delay_ += unit_read_delay_ * self.access_num / self.port_num
        elif self.access_type == 'write':
            unit_write_delay_ = unit_delay(self.cell_type, self.technology, self.port_type)
            delay_ += unit_write_delay_ * self.access_num / self.port_num
        return delay_


class DRAM(DigitalStorage):
    def __init__(self):
        super().__init__(cell_type='DRAM',
                         size,
                         technology,
                         port_num,
                         port_type,
                         access_type,
                         access_num,
                         arrangement)


class SRAM(DigitalStorage):
    def __init__(self):
        super().__init__(cell_type='SRAM',
                         size,
                         technology,
                         port_num,
                         port_type,
                         access_type,
                         access_num,
                         arrangement)


class RegisterFile(DigitalStorage):
    def __init__(self):
        super().__init__(cell_type='RF',
                         size,
                         technology,
                         port_num,
                         port_type,
                         access_type,
                         access_num,
                         arrangement)


class DFF(DigitalStorage):
    def __init__(self):
        super().__init__(cell_type='DFF',
                         size,
                         technology,
                         port_num,
                         port_type,
                         access_type,
                         access_num,
                         arrangement)

    def performance(self):
        pass


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


class Passive_SC(AnalogCell):
    def __init__(self):
        super().__init__()

    def performance(self):
        return [energy, area, delay]


class Voltage_WTA(AnalogCell):
    def __init__(self):
        super().__init__()

    def performance(self):
        return [energy, area, delay]


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
class ChargeOperation(object):
    """docstring for charge-domain analog operations"""

    def __init__(self,
                 VDD):
        self.VDD = VDD

    def MatrixMultiplier_active(self,
                                input,  # vector
                                weight,  # vector, floating point, normalized to [-1,1]
                                CDAC_reso,  # including sign-bit
                                C_unit,
                                C2,
                                opamp_gain):
        A = opamp_gain
        CDAC = np.zeros((CDAC_reso))
        for i in range(CDAC_reso):
            CDAC[i] = C_unit * 2 ** (CDAC_reso - i)

        weight = np.round(weight * (2 ** (CDAC_reso - 1) - 1))
        k = C2 * (A + 1) / (C2 * (A + 1) + np.sum(np.multiply(CDAC, weight)))
        mu = np.sum(np.multiply(CDAC, weight)) / C2 * A / (A + 1)

        for c in range(len(input)):
            weight[c] = mu[c]
            for i in range(c, 12, 1):
                weight[c] *= k[i]
        output = np.sum(np.multiply(weight, input))
        return [output, area_, energy_, delay_]

    def MatrixMultiplier_passive(self,
                                 input,  # vector
                                 weight,  # vector, floating point, normalized to [-1,1]
                                 CDAC_reso,  # including sign-bit
                                 C_unit,
                                 C2):
        CDAC = np.zeros((CDAC_reso))
        for i in range(CDAC_reso):
            CDAC[i] = C_unit * 2 ** (CDAC_reso - i)

        weight = np.round(weight * (2 ** (CDAC_reso - 1) - 1))
        k = C2 / (C2 + np.sum(np.multiply(CDAC, weight)))
        mu = np.sum(np.multiply(CDAC, weight)) / C2

        for c in range(len(input)):
            weight[c] = mu[c]
            for i in range(c, 12, 1):
                weight[c] *= k[i]
        output = np.sum(np.multiply(weight, input))
        return [output, area_, energy_, delay_]


########################################################################################################################
class DomainChecker(object):
    def __init__(self):
        pass


class DomainConverter(object):
    """docstring for analog domain conversion"""

    def __init__(self):
        pass

    def voltage2charge(self):
        pass

    def charge2voltage(self):
        pass

    def voltage2current(self):
        pass

    def current2voltage(self):
        pass

    def voltage2time(self):
        pass

    def time2voltage(self):
        pass

    def current2charge(self):
        pass

    def charge2current(self):
        pass

    def current2time(self):
        pass

    def time2current(self):
        pass

    def charge2time(self):
        pass

    def time2charge(self):
        pass


########################################################################################################################
class PostADCThreshold(object):
    """docstring for thresholding functions after ADC"""

    def __init__(self):
        pass

    def threshold(self, x, type):
        if type == 'sign':
            y = np.sign(x)
            delay = 0
            energy = 0
        if type == 'min':
            y = np.min(x)
            delay = 0
            energy = 0
        if type == 'max':
            y = np.max(x)
            delay = 0
            energy = 0
        if type == 'mean':
            y = np.mean(x)
            delay = 0
            energy = 0
        if type == 'sigmoid':
            y = 1 / (1 + np.exp(-x))
            delay = 0
            energy = 0
        if type == 'relu':
            y = x * (x > 0)
            delay = 0
            energy = 0
        if type == 'accumulate':
            y = np.sum(x)
            delay = 0
            energy = 0
        return y, delay, energy
