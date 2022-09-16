import numpy as np


class Pixel(object):
    """docstring for pixel"""

    def __init__(self,
                 pitch,
                 technology,
                 type
                 ):
        self.pitch = pitch
        self.technology = technology
        self.type = type

    def exposure(self,
                 type,
                 n_rows,
                 n_columns):
        if type == 'rolling_shutter':
            n_rows = 1
            n_columns = self.size[1]
        if type == 'multi_rolling_shutter':
            n_rows = n_rows
            n_columns = self.size[1]
        if type == 'global_shutter':
            n_rows = self.size[0]
            n_columns = self.size[1]
        if type == 'rolling_band_shutter':
            n_rows = n_rows
            n_columns = n_columns
        if type == 'pixel_wise_shutter':
            n_rows = 1
            n_columns = 1
        return n_rows, n_columns


class APS(Pixel):
    def __init__(self):
        super().__init__()

    def performance(self):
        pass


class DPS(Pixel):
    def __init__(self):
        super().__init__()

    def performance(self):
        pass


class PWM(Pixel):
    def __init__(self):
        super().__init__()

    def performance(self):
        pass


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
class AnalogStorage(object):
    """docstring for DataStorage"""

    def __init__(self,
                 capacitance,
                 droop_rate,
                 holding_time,
                 supply_voltage,
                 size,
                 technology,
                 access_type,
                 access_num,
                 arrangement):
        self.capacitance = capacitance
        self.droop_rate = droop_rate
        self.holding_time = holding_time
        self.supply_voltage = supply_voltage
        self.size = size
        self.technology = technology
        self.access_type = access_type
        self.access_num = access_num
        self.arrangement = arrangement

    def area(self):
        pass

    def energy(self):
        pass

    def delay(self):
        pass

    def stored_value(self,
                     input):
        output = input * (1 - self.holding_time * self.droop_rate)
        return output


########################################################################################################################
class AnalogCell(object):
    def __init__(self):
        pass


class Current_DAC(AnalogCell):
    def __init__(self):
        super().__init__()

    def performance(self):
        return [energy, area, delay]


class Current_Mirror(AnalogCell):
    def __init__(self):
        super().__init__()

    def performance(self,
                    VDD,
                    I,
                    t):
        return [energy, area, delay]


class Voltage_Sampler(AnalogCell):
    def __init__(self):
        super().__init__()

    def performance(self):
        return [energy, area, delay]


class Comparator(AnalogCell):
    def __init__(self):
        super().__init__()

    def performance(self):
        return [energy, area, delay]


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

    def area(self):
        pass

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
class AnalogScalarDistance(object):
    """docstring for analog scalar distance"""

    def __init__(self,
                 VDD):
        self.VDD = VDD

    def signed_multiply(self,
                        input,
                        weight,
                        domain):
        if domain == 'charge':
            pass

    def unsigned_multiply(self):
        pass

    def l1(self):
        pass

    def l2(self):
        pass

    def square(self):
        pass

    def none(self):
        pass


class AnalogVectorDistance(object):
    """docstring for analog vector distance"""

    def __init__(self,
                 VDD):
        self.VDD = VDD

    def accumulation(self):
        pass

    def average(self):
        pass

    def none(self):
        pass


########################################################################################################################
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
