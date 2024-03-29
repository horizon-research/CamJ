import numpy as np

from camj.analog.component import ColumnAmplifier
from camj.general.enum import ProcessDomain

class EventificationUnit(object):
    """docstring for EventificationUnit"""
    def __init__(
        self, 
        event_threshold = 0.3,
        # performance parameters
        load_capacitance = 1e-12,  # [F]
        input_capacitance = 1e-12,  # [F]
        t_sample = 2e-6,  # [s]
        t_hold = 10e-3,  # [s]
        supply = 1.8,  # [V]
        gain_cl = 1,
        differential = False,
        # noise parameters
        gain = 1.0,
        enable_prnu = False,
        prnu_std = 0.001,
        enable_offset = False,
        pixel_offset_voltage = 0.1,
        col_offset_voltage = 0.05
    ):
        super(EventificationUnit, self).__init__()

        self.name = "Eventification"
        
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.VOLTAGE]
        self.output_domain = ProcessDomain.VOLTAGE

        # set input/output driver
        self.input_need_driver = False
        self.output_driver = True

        # this column amplifier is used to read the absolute value.
        self.colamp_model1 = ColumnAmplifier(
            load_capacitance = load_capacitance,
            input_capacitance = input_capacitance,
            t_sample = t_sample,
            t_hold = t_hold,
            supply = supply,
            gain_cl = gain_cl,
            differential = differential,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std,
            enable_offset = enable_offset,
            pixel_offset_voltage = pixel_offset_voltage,
            col_offset_voltage = col_offset_voltage
        )

        # this column amplifier is used to scale the current frame value based on event threshold.
        self.colamp_model2 = ColumnAmplifier(
            load_capacitance = load_capacitance,
            input_capacitance = input_capacitance,
            t_sample = t_sample,
            t_hold = t_hold,
            supply = supply,
            gain_cl = gain_cl,
            differential = differential,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std,
            enable_offset = enable_offset,
            pixel_offset_voltage = pixel_offset_voltage,
            col_offset_voltage = col_offset_voltage
        )

    def energy(self):
        return self.colamp_model1.energy() + self.colamp_model2.energy()

    def noise(self, input_signal_list):
        if len(input_signal_list) != 2:
            raise Exception("Input signal list to 'EventificationUnit' need to a length of 2.")

        # compute the absolute difference
        abs_val = np.abs(input_signal_list[0] - input_signal_list[1])
        _, abs_signal = self.colamp_model1.noise([abs_val])
        _, second_signal = self.colamp_model2.noise([input_signal_list[1]])

        return (self.name, abs_signal + second_signal)
