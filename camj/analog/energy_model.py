import numpy as np
from camj.analog.energy_utils import gm_id, get_pixel_parasitic, parallel_impedance, get_delay, get_nominal_supply


class PinnedPhotodiodeEnergy(object):
    """Pinned photodiode (PD).

    The model only contains the dynamic energy of the PD's internal capacitance.

    Args:
        pd_capacitance (float): [unit: F] the capacitance of PD.
        pd_supply (float): [unit: V] supply voltage of pixel.
    """

    def __init__(self,
                 pd_capacitance=100e-15,  # [F]
                 pd_supply=3.3  # [V]
                 ):
        self.pd_capacitance = pd_capacitance
        self.pd_supply = pd_supply

    def energy(self):
        energy = self.pd_capacitance * (self.pd_supply ** 2)
        return energy


class ActivePixelSensorEnergy(PinnedPhotodiodeEnergy):
    """Active pixel sensor (APS).

    The model includes photodiode (PD), floating diffusion (FD), source follower (SF),
    and parasitic capacitance on the SF's readout wire.

    Our APS model supports energy estimation for both 3T-APS and 4T-APS. Users need to define
    `num_transistor` to get the correct energy estimation.

    Args:
        pd_capacitance (float): [unit: F] the capacitance of PD.
        pd_supply (float): [unit: V] supply voltage of pixel.
        dynamic_sf (bool): using dynamic SF or not. In most cases, the in-pixel SF is not dynamic, 
            meaning that it is statically-biased by a constant current. However, some works [JSSC-2021]
            use dynamic SF to save energy.
        output_vs (float): [unit: V] voltage swing at SF's output node. Typically it is 
            one or two units of threshold voltage smaller than pd_supply, depending on 
            the pixel's circuit structure.
        num_transistor (int): {3 or 4}. It defines using 3T APS or 4T APS.
        num_readout (int): {2 or 1}. It defines enabling CDS or not.
        load_capacitance (float): [unit: F] load capacitance at the SF's output node.
        tech_node (int): [unit: nm] pixel's process node.
        pitch (float): [unit: um] pixel pitch size (width or height).
        array_vsize (int): the vertical size of the entire pixel array. This is used to estimate 
            the parasitic capacitance on the SF's readout wire.

    References Link:
        * JSSC-2021: A 51-pJ/Pixel 33.7-dB PSNR 4× Compressive CMOS Image Sensor With Column-Parallel Single-Shot Compressive Sensing.
            https://ieeexplore.ieee.org/abstract/document/9424987
    """

    def __init__(
            self,
            pd_capacitance,
            pd_supply,
            dynamic_sf=False,
            output_vs=1,  # [V]
            num_transistor=4,
            fd_capacitance=10e-15,  # [F]
            num_readout=2,
            load_capacitance=1e-12,  # [F]
            tech_node=130,  # [nm]
            pitch=4,  # [um]
            array_vsize=128
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
        """Calculate Energy

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
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
            ) * self.output_vs ** 2
        else:
            energy_sf = (
                self.load_capacitance +
                get_pixel_parasitic(self.array_vsize, self.tech_node, self.pitch)
            ) * self.pd_supply * self.output_vs

        energy_pd = super(ActivePixelSensorEnergy, self).energy()
        energy = energy_pd + energy_fd + self.num_readout * energy_sf

        return energy

    def _impedance(
            self,
            sf_bias_current=2e-6  # [A]
    ):
        input_impedance = None

        gm_id_ratio = 16
        gm_n = gm_id_ratio * sf_bias_current
        output_impedance = 1 / gm_n
        return [input_impedance, output_impedance]

    def _capacitance(self):
        input_capacitance = None
        output_capacitance = self.load_capacitance
        return [input_capacitance, output_capacitance]


class DigitalPixelSensorEnergy(ActivePixelSensorEnergy):
    """ Digital pixel sensor (DPS).

    The model consists of an APS and an in-pixel ADC.

    Args:
        pd_capacitance (float): [unit: F] the capacitance of PD.
        pd_supply (float): [unit: V] supply voltage of pixel.
        dynamic_sf (bool): using dynamic SF or not. In most cases, the in-pixel SF is not dynamic, 
            meaning that it is statically-biased by a constant current. However, some works [JSSC-2021]
            use dynamic SF to save energy.
        output_vs (float): [unit: V] voltage swing at SF's output node. Typically it is 
            one or two units of threshold voltage smaller than pd_supply, depending on 
            the pixel's circuit structure.
        num_transistor (int): {3 or 4}. It defines using 3T APS or 4T APS.
        num_readout (int): {2 or 1}. It defines enabling CDS or not.
        load_capacitance (float): [unit: F] load capacitance at the SF's output node.
        tech_node (int): [unit: nm] pixel's process node.
        pitch (float): [unit: um] pixel pitch size (width or height).
        array_vsize (int): the vertical size of the entire pixel array. This is used to estimate 
            the parasitic capacitance on the SF's readout wire.
        adc_type (str): the actual ADC type. Please check ADC class for more details.
        adc_fom (float): [unit: J/conversion] ADC's Figure-of-Merit, expressed by energy per conversion.
        adc_resolution (int): ADC's resolution.
    """

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
            pd_capacitance=pd_capacitance,
            pd_supply=pd_supply,
            dynamic_sf=dynamic_sf,
            output_vs=output_vs,
            num_transistor=num_transistor,
            fd_capacitance=fd_capacitance,
            num_readout=num_readout,
            load_capacitance=load_capacitance,
            tech_node=tech_node,
            pitch=pitch,
            array_vsize=array_vsize
        )
        self.adc_type = adc_type
        self.adc_fom = adc_fom
        self.adc_reso = adc_reso

    def energy(self):
        """Calculate Energy

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        energy_aps = super(DigitalPixelSensorEnergy, self).energy()
        energy_adc = AnalogToDigitalConverterEnergy(self.pd_supply, self.adc_type, self.adc_fom, self.adc_reso).energy()
        energy = energy_aps + energy_adc

        return energy


class PulseWidthModulationPixelEnergy(PinnedPhotodiodeEnergy):
    """ Pulse-Width-Modulation (PWM) Pixel.

    The model is based on the design in [JSSC-2020] and [ISSCC-2022].
    The model consists of a photodiode (PD), a ramp signal generator, and a comparator.
    The comparator output toggles when the ramp signal is smaller than the pixel voltage at PD.

    Args:
        pd_capacitance (float): [unit: F] PD capacitance.
        pd_supply (float): [unit: V] PD voltage supply.
        array_vsize (int): the vertical size of the entire pixel array. This is used to estimate the parasitic capacitance on the SF's readout wire.
        ramp_capacitance (float): [unit: F] capacitance of ramp signal generator.
        gate_capacitance (float): [unit: F] the gate capacitance of readout transistor.
        num_readout (int): number of read from pixel.

    References Link:
        * JSSC-2020: A 0.5-V Real-Time Computational CMOS Image Sensor With Programmable Kernel for Feature Extraction.
            https://ieeexplore.ieee.org/abstract/document/9250500
        * ISSCC-2022: A 0.8V Intelligent Vision Sensor with Tiny Convolutional Neural Network and Programmable Weights Using Mixed-Mode Processing-in-Sensor Technique for Image Classification.
            https://ieeexplore.ieee.org/abstract/document/9731675
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
        """Calculate Energy

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        energy_parasitics = self.array_vsize / 3 * 10e-15 * (self.pd_supply ** 2)

        energy_ramp = self.ramp_capacitance * (self.pd_supply ** 2)
        energy_comparator = self.gate_capacitance * (self.pd_supply ** 2)
        energy_pd = super(PulseWidthModulationPixelEnergy, self).energy()
        energy = energy_pd + self.num_readout * (energy_ramp * 2 + energy_comparator + energy_parasitics)

        return energy


class ColumnAmplifierEnergy(object):
    """ Switched-capacitor amplifier.
    
    The model is based on Fig. 13.5 in [Book-Razavi].
    The model includes an input capacitor, a feedback capacitor, a load capacitor, and an amplifier.
    This amplifier can be used either as pixel array's column amplifier or as a general-purpose switched-capacitor amplifier,
    such as switched-capacitor integrator, switched-capacitor subtractor, and switched-capacitor multiplier.

    Args:
        load_capacitance (float): [unit: F] load capacitance.
        input_capacitance (float): [unit: F] input capacitance.
        t_sample (float): [unit: s] sampling time, which mainly consists of the amplifier's 
            settling time.
        t_hold (float): [unit: s] holding time, during which the amplifier is turned on and
            consumes power relentlessly.
        supply (float): [unit: V] supply voltage.
        gain_close (int): amplifier's closed-loop gain. This gain describes the ratio of 
            ``input_capacitance`` over feedback capacitance.
        gain_open (int): amplifier's open-loop gain. This gain is used to determine the 
            amplifier's bias current by gm/id method.
        differential (bool): if using differential-input amplifier or single-input amplifier.

    References Link:
        * Book-Razavi: Design of Analog CMOS Integrated Circuits (Second Edition)
    """

    def __init__(
            self,
            load_capacitance=1e-12,  # [F]
            input_capacitance=1e-12,  # [F]
            t_sample=2e-6,  # [s]
            t_hold=10e-3,  # [s], FIXME: name changed!
            supply=1.8,  # [V]
            gain_close=2,  # FIXME: name changed!
            gain_open=256,
            differential=False,
    ):
        self.load_capacitance = load_capacitance
        self.input_capacitance = input_capacitance
        self.t_sample = t_sample
        self.t_hold = t_hold
        self.supply = supply
        self.gain_close = gain_close
        self.gain_open = gain_open
        self.fb_capacitance = self.input_capacitance / self.gain_close
        [self.i_opamp, self.gm] = gm_id(
            load_capacitance=self.load_capacitance,
            gain=self.gain_open,
            bandwidth=1 / self.t_sample,
            differential=differential,
            inversion_level='moderate'
        )
        self.gd = self.gm / 100  # gd<<gm

    def energy(self):
        """Calculate Energy

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        energy_opamp = self.supply * self.i_opamp * self.t_hold
        energy = energy_opamp + (self.input_capacitance + self.fb_capacitance + self.load_capacitance) \
                 * (self.supply ** 2)
        # print(self.i_opamp, energy_opamp)
        return energy

    def _impedance(self):
        input_impedance = float('inf')

        gm_n = gm_p = self.gm
        gd_n = gd_p = self.gd
        output_impedance = parallel_impedance([gm_n * (1 / gd_n) ** 2, gm_p * (1 / gd_p) ** 2])
        return [input_impedance, output_impedance]

    def _capacitance(self):
        input_capacitance = self.input_capacitance
        output_capacitance = self.load_capacitance
        return [input_capacitance, output_capacitance]


class SourceFollowerEnergy(object):
    """ Source follower (SF) with constant current bias.

    This model is applicable to not only the simplest single-transistor source follower 
    but also flipped-voltage-follower (FVF).

    Args:
        load_capacitance (float): [unit: F] load capacitance.
        supply (float): [unit: V] supply voltage.
        output_vs (float): [unit: V] voltage swing at the SF's output node.
        bias_current (float): [unit: A] bias current.
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
        """Calculate Energy

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        energy = self.load_capacitance * self.supply * self.output_vs
        return energy

    def _impedance(self):
        input_impedance = float('inf')

        gm_id_ratio = 16
        gm_n = gm_id_ratio * self.bias_current
        output_impedance = 1 / gm_n
        return [input_impedance, output_impedance]

    def _capacitance(self):
        input_capacitance = 0
        output_capacitance = self.load_capacitance
        return [input_capacitance, output_capacitance]


class ActiveAnalogMemoryEnergy(object):
    """ Analog memory with active feedback.

    The model is based on the design in [JSSC-2004].
    The model consists of a sample capacitor, a compensation capacitor, and an amplifier 
    which holds the stored analog data through feedback.

    Args:
        sample_capacitance (float): [unit: F] sample capacitance.
        comp_capacitance (float): [unit: F] compensation capacitance
        t_sample (float): [unit: s] sampling time, which mainly consists of the amplifier's settling time.
        t_hold (float): [unit: s] holding time, during which the amplifier is turned on and consumes
            power relentlessly.
        supply (float): [unit: V] supply voltage.

    References Link:
        * JSSC-2004: A 10-nW 12-bit accurate analog storage cell with 10-aA leakage. 
            https://ieeexplore.ieee.org/abstract/document/1347329
    """

    def __init__(
            self,
            sample_capacitance=2e-12,  # [F]
            comp_capacitance=2.5e-12,  # [F]
            t_sample=1e-6,  # [s]
            t_hold=10e-3,  # [s]
            supply=1.8,  # [V]
    ):
        self.sample_capacitance = sample_capacitance
        self.comp_capacitance = comp_capacitance
        self.t_sample = t_sample
        self.t_hold = t_hold
        self.supply = supply
        [self.i_opamp, self.gm] = gm_id(
            load_capacitance=self.comp_capacitance,
            gain=300,
            bandwidth=1 / self.t_sample,
            differential=True,
            inversion_level='moderate'
        )
        self.gd = self.gm / 100

    def energy(self):
        """Calculate Energy

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        energy_opamp = self.supply * self.i_opamp * self.t_hold
        energy = energy_opamp + (self.sample_capacitance + self.comp_capacitance) * (self.supply ** 2)
        return energy

    def _impedance(self):
        input_impedance = float('inf')

        gm_n = gm_p = self.gm
        gd_n = gd_p = self.gd
        output_impedance = parallel_impedance([gm_n * (1 / gd_n) ** 2, gm_p * (1 / gd_p) ** 2])
        return [input_impedance, output_impedance]

    def _capacitance(self):
        input_capacitance = self.sample_capacitance
        output_capacitance = self.comp_capacitance
        return [input_capacitance, output_capacitance]


class PassiveAnalogMemoryEnergy(object):
    """ Analog memory without active feedback.
    
    The model only contains a sample capacitor. Compared to ActiveAnalogMemory it has higher data leakage rate.

    Args:
        sample_capacitance (float): [unit: F] sample capacitance.
        supply (float): [unit: V] supply voltage.
    """

    def __init__(
            self,
            sample_capacitance=1e-12,  # [F] FIXME: name changed!
            supply=1.8,  # [V]
    ):
        self.sample_capacitance = sample_capacitance
        self.supply = supply

    def energy(self):
        """Calculate Energy

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        energy = self.sample_capacitance * (self.supply ** 2)
        return energy

    def _impedance(self):
        input_impedance = float('inf')
        output_impedance = float('inf')
        return [input_impedance, output_impedance]

    def _capacitance(self):
        input_capacitance = self.sample_capacitance
        output_capacitance = 0
        return [input_capacitance, output_capacitance]


class DigitalToCurrentConverterEnergy(object):  # FIXME: function changed! may delete this class.
    """ Current digital-to-analog converter.

    The model consists of a constant current path and a load capacitor.

    Args:
        supply (float): [unit: V] supply voltage.
        load_capacitance (float): [unit: F] load capacitance.
        t_readout (float): [unit: s] readout time, during which the constant current drives
            the load capacitance from 0 to VDD.
    """

    def __init__(
            self,
            supply=1.8,  # [V]
            load_capacitance=2e-12,  # [F]
            t_readout=16e-6,  # [s]
    ):
        self.supply = supply
        self.load_capacitance = load_capacitance
        self.t_readout = t_readout
        self.i_dc = self.load_capacitance * self.supply / self.t_readout

    def energy(self):
        energy = self.supply * self.i_dc * self.t_readout
        return energy


class CurrentMirrorEnergy(object):
    """ Current mirror.
    
    The model consists of a constant current path and a load capacitor.

    Args:
        supply (float): [unit: V] supply voltage.
        load_capacitance (float): [unit: F] load capacitance.
        t_readout (float): [unit: s] readout time, during which the constant current drives
            the load capacitance from 0 to VDD.
        i_dc (float): [unit: A] the constant current. If ``i_dc == None``, then i_dc is
            estimated from the other parameters.
    """

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
        """Calculate Energy

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        energy = self.supply * self.i_dc * self.t_readout
        return energy


class PassiveSwitchedCapacitorArrayEnergy(object):
    """ Passive switched-capacitor array.

    The model consists of a list of capacitors and a list of voltages that corresponds to 
    the voltage swing at each capacitor. The model is used to represent all passive 
    switched-capacitor computational circuits, including charge-redistribution-based MAC operation.

    Args:
        capacitance_array (array, float): [unit: F] a list of capacitors.
        vs_array (array, float): [unit: V] a list of voltages that corresponds to the voltage swing at each capacitor.
    """

    def __init__(
            self,
            capacitance_array,
            vs_array
    ):
        self.capacitance_array = capacitance_array
        self.vs_array = vs_array

    def energy(self):
        """Calculate Energy

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        energy = np.sum(np.multiply(self.capacitance_array, [vs ** 2 for vs in self.vs_array]))
        return energy


class MaximumVoltageEnergy(object):
    """ A circuit that outputs the maximum voltage among the input voltages.

    The model is based on the design in [Sensors-2020].
    The model consists of a constant current path, a group of common-source amplifiers, and a load capacitor.
    The number of common-source amplifiers matches the number of input voltages.
    Note that all common-source amplifiers share one bias current so the bias current doesn't scale with the number of input voltages.

    Args:
        supply (float): [unit: V] supply voltage.
        t_hold (float): [unit: s] holding time, during which the circuit is turned on and consumes power relentlessly.
        t_readout (float): [unit: s] readout time, during which the maximum voltage is output.
        load_capacitance (float): [unit: F] load capacitance
        gain (float): open-loop gain of the common-source amplifier.

    References Link:
        * Sensors-2020: Design of an Always-On Image Sensor Using an Analog Lightweight Convolutional Neural Network.
            https://www.mdpi.com/1424-8220/20/11/3101
    """

    def __init__(
            self,
            supply=1.8,  # [V]
            t_hold=30e-3,  # [s] FIXME: name changed!
            t_readout=1e-6,  # [s] FIXME: name changed!
            load_capacitance=1e-12,  # [F]
            gain=10
    ):
        self.supply = supply
        self.load_capacitance = load_capacitance
        self.t_hold = t_hold
        self.t_readout = t_readout
        self.gain = gain

    def energy(self):
        """Calculate Energy

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        i_bias, _ = gm_id(
            self.load_capacitance,
            gain=self.gain,
            bandwidth=1 / self.t_readout,
            differential=True,
            inversion_level='moderate'
        )
        energy_bias = self.supply * (0.5 * i_bias) * self.t_hold
        energy_amplifier = self.supply * i_bias * self.t_readout
        energy = energy_bias + energy_amplifier
        return energy


class ComparatorEnergy(object):
    """ Dynamic voltage comparator.

    Args:
        supply (float): [unit: V] supply voltage.
        i_bias (float): [unit: A] bias current of the circuit.
        t_readout (float): [unit: s] readout time, during which the comparison is finished.
    """

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
        """Calculate Energy

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        energy = self.supply * self.i_bias * self.t_readout
        return energy


class AnalogToDigitalConverterEnergy(object):
    """ Analog-to-digital converter.

    Args:
        supply (float): [unit: V] supply voltage.
        type (str): ADC type.
        fom (float): [unit: J/conversion] ADC's Figure-of-Merit, expressed by energy per conversion.
        resolution (int): ADC resolution.
    """

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
        """Calculate Energy

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        energy = self.fom * (2 ** self.resolution)
        return energy

    def _quantization_noise(self):  # [unit: V]
        LSB = self.supply / 2 ** (self.resolution - 1)
        return 1 / 12 * LSB ** 2


class GeneralCircuitEnergy(object):
    """ Energy model for general circuits from first principle.

    Args:
        supply (float): [unit: V] supply voltage.
        i_dc (float): [unit: A] direct current of the circuit.
        t_operation (float): [unit: s] operation time, during which the circuit completes its particular operation.
    """

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
        """Calculate Energy

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        energy = self.supply * self.i_dc * self.t_operation
        return energy
