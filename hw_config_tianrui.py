import numpy as np


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

    def stored_value(self, input):
        input = input * (1 - self.holding_time * self.droop_rate)
        return input


class ADC(object):
    """docstring for differential-input rail-to-rail ADC"""

    def __init__(
            self,
            type,
            supply_voltage,
            resolution):
        self.type = type
        self.supply_voltage = supply_voltage
        self.resolution = resolution

    def area(self):
        pass

    def energy(self):
        pass

    def delay(self):
        pass

    def quantization_noise(self):  # [unit: V]
        LSB = self.supply_voltage / 2 ** (self.resolution - 1)
        return 1 / 12 * LSB ** 2


class ChargeOperation(object):
    """docstring for charge-domain analog operations"""

    def __init__(self,
                 inputQ,
                 outputQ):
        self.inputQ = inputQ
        self.outputQ = outputQ

    def MatrixMultiplier_active(self,
                                weight,  # CDAC_reso-bit digital code
                                CDAC_reso,
                                C_unit,
                                C2,
                                opamp_gain):
        A = opamp_gain
        CDAC = np.zeros((CDAC_reso))
        for i in range(CDAC_reso):
            CDAC[i] = C_unit * 2 ** (CDAC_reso - i)
        k = C2 * (A + 1) / (C2 * (A + 1) + np.sum(np.multiply(CDAC, weight)))
        mu = np.sum(np.multiply(CDAC, weight)) / C2 * A / (A + 1)
        return [self.outputQ, area_, energy_, delay_]

    def MatrixMultiplier_passive(self,
                                 weight,  # CDAC_reso-bit digital code
                                 CDAC_reso,
                                 C_unit,
                                 C2):
        CDAC = np.zeros((CDAC_reso))
        for i in range(CDAC_reso):
            CDAC[i] = C_unit * 2 ** (CDAC_reso - i)
        k = C2 / (C2 + np.sum(np.multiply(CDAC, weight)))
        mu = np.sum(np.multiply(CDAC, weight)) / C2
        return [self.outputQ, area_, energy_, delay_]


class VoltageOperation(object):
    """docstring for voltage-domain analog operations"""

    def __init__(self,
                 inputV,
                 outputV):
        self.inputV = inputV
        self.outputV = outputV


class CurrentOperation(object):
    """docstring for current-domain analog operations"""

    def __init__(self,
                 inputI,
                 outputI):
        self.inputI = inputI
        self.outputI = outputI

    def add(self):
        pass


class TimeOperation(object):
    """docstring for charge-domain analog operations"""

    def __init__(self):
        pass

    def exposure(self):
        pass


########################################################################################################################

class ProcessUnit(object):
    """docstring for ProcessUnit"""

    def __init__(
            self,
            name: str,
            domain: int,
            location: int,
            throughput: float,
            latency: float,
            power: float,
            area: float,
    ):
        super(ProcessUnit, self).__init__()

        self.name = name
        self.domain = domain
        self.location = location
        self.throughput = throughput
        self.latency = latency
        self.power = power
        self.area = area

    def set_input_buffer(input_buffer):
        self.input_buffer = input_buffer

    def set_output_buffer(output_buffer):
        self.output_buffer = output_buffer


compute_sum_16_unit = ProcessUnit(
    name="ComputeSum16",
    domain=ANALOG,
    location=SENSOR_LAYER,
    throughput= ??,
latency = ??,
power = ??,
area = ??
)

compute_sum_16_unit.set_input_buffer(input_data)
compute_sum_16_unit.set_output_buffer(adc)

div_by_16_unit = ProcessUnit(
    name="DivBy16",
    domain=DIGITAL,
    location=COMPUTE_LAYER,
    throughput= ??,
latency = ??,
power = ??,
area = ??
)

div_by_16_unit.set_input_buffer(adc)
div_by_16_unit.set_output_buffer(line_buffer1)

conv2d_unit = ProcessUnit(
    name="Conv2D_1",
    domain=DIGITAL,
    location=COMPUTE_LAYER,
    throughput= ??,
latency = ??,
power = ??,
area = ??
)

conv2d_unit.set_input_buffer(line_buffer1)
conv2d_unit.set_output_buffer(scratchpad1)
