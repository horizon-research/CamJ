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
                 size,
                 technology,
                 access_type,
                 access_num,
                 arrangement):
        self.capacitance = capacitance
        self.droop_rate = droop_rate
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

    def accuracy(self):
        pass


########################################################################################################################
line_buffer1 = SRAM(
    storage_type=LINE_BUFFER,
    impl=SRAM,
    size=[ROW, COLUMN],
    mem_technology=65,
    port=[4],
    port_accessibility=[SHARED],
    access_stage=["DivBy16", "Conv2D_1"],
    location=COMPUTE_LAYER,
)

scratchpad1 = DigitalStorage(
    type=SCRATCHPAD,
    impl=SRAM,
    mem_technology=65,
    port=[4],
    port_accessibility=[SHARED],
    access_stage=["Conv2D_1"],
    location=STORAGE_LAYER,
)


class ADC(object):
    """docstring for ADC"""

    def __init__(
            self,
            type: INT,
            pixel_adc_ratio: tuple,
            location=location
    ):
        super(ADC, self).__init__()
        self.type
        self.pixel_adc_ratio
        self.location = location


adc = ADC(
    SINGLE_SLOPE,  # ADC type?
    pixel_adc_ratio=(1, 256),  # or (1, 1), (4, 4)
    location=SENSOR_LAYER,
)


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
