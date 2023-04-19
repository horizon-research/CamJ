"""Analog Component Interface

This module contains the high-level interface to configure analog component and performs 
functional and energy simulation.

Each analog component class contains two main functions, ``energy()`` and ``noise(input_signals)``.
``energy()`` function calculates the energy of the analog component. ``noise(input_signals)`` function
simulates the functional properties with the given input signals.

Examples:
        To run energy simulation:

        >>> energy_number = [analog_component].energy()

        To run functional simulation:

        >>> output_signals = [analog_component].noise(input_signals)

"""

# TODO [Tianrui]: check if we need to consider input noise in column amplifier

import numpy as np
import time

# import local modules
from camj.analog.function_utils import default_functional_simulation, _cap_thermal_noise,\
                                _single_pole_rc_circuit_thermal_noise
from camj.analog.energy_model import  ColumnAmplifierEnergy, SourceFollowerEnergy,\
                                ActiveAnalogMemoryEnergy, PassiveAnalogMemoryEnergy,\
                                DigitalToCurrentConverterEnergy, CurrentMirrorEnergy,\
                                ComparatorEnergy, PassiveSwitchedCapacitorArrayEnergy,\
                                AnalogToDigitalConverterEnergy, DigitalToCurrentConverterEnergy,\
                                MaximumVoltageEnergy, GeneralCircuitEnergy, ActivePixelSensorEnergy,\
                                DigitalPixelSensorEnergy, PulseWidthModulationPixelEnergy
from camj.analog.function_model import ColumnwiseFunc, PixelwiseFunc, FloatingDiffusionFunc,\
                                CurrentMirrorFunc, ComparatorFunc, AnalogToDigitalConverterFunc,\
                                PassiveSwitchedCapacitorArrayFunc, CorrelatedDoubleSamplingFunc,\
                                AbsoluteDifferenceFunc, MaximumVoltageFunc, PhotodiodeFunc
from camj.general.enum import ProcessDomain

# Active pxiel sensor
class ActivePixelSensor(object):
    """Active Pixel Sensor Model

    Our APS model includes modeling photodiode (PD), floating diffusion (FD), source follower (SF),
    and parasitic during the readout. This APS model supports energy estimation for both 3T-APS and
    4T-APS. Users need to define ``num_transistor`` to get the correct energy estimation.

    Input/Output domains:
        * input domain: ``ProcessDomain.OPTICAL``.
        * output domain: ``ProcessDomain.VOLTAGE``.

    Args:
        pd_capacitance (float): [unit: F] the capacitance of PD.
        pd_supply (float): [unit: V] supply voltage of pixel.
        dynamic_sf (bool): using dynamic SF or not. In most cases, the in-pixel SF is not dynamic, 
            meaning that it is statically-biased by a constant current. However, some works [JSSC-2021]
            use dynamic SF to save energy.
        output_vs (float): [unit: V] voltage swing at SF's output node. Typically it is one or two 
            units of threshold voltage smaller than pd_supply, depending on the pixel's circuit structure.
        num_transistor (int): {3 or 4}. It defines using 3T APS or 4T APS.
        enable_cds (bool): enabling CDS or not.
        fd_capacitance (float): the capacitance of FD.
        load_capacitance (float): [unit: F] load capacitance at the SF's output node.
        tech_node (int): [unit: nm] pixel's process node.
        pitch (float): [unit: um] pixel pitch size (width or height).
        array_vsize (int): the vertical size of the entire pixel array. This is used to estimate 
            the parasitic capacitance on the SF's readout wire.
        dark_current_noise (float): average dark current noise in unit of electrons (e-).
        enable_dcnu (bool): flag to enable dark current non-uniformity, the default value is ``False``.
        enable_prnu (bool): flag to enable PRNU. Default value is ``False``.
        dcnu_std (float): dcnu standard deviation percentage. it is relative number respect
            to ``dark_current_noise``, the dcnu standard deviation is,
            ``dcnu_std`` * ``dark_current_noise``, the default value is ``0.001``. 
        fd_gain (float): the gain of FD, the default value is ``1.0``.
        fd_noise (float): the standard deviation of FD read noise, the default value is ``None``. If
            users do not specific this parameter, CamJ will calculate the noise STD based on the kTC
            noise.
        fd_prnu_std (float): relative PRNU standard deviation respect to FD gain. 
            PRNU gain standard deviation = prnu_std * gain. The default value is ``0.001``.
        sf_gain (float): the gain of SF, the default value is ``1.0``.
        sf_noise (float): the stadard deviation of SF read noise, the default value is ``None``. If
            users do not specific this parameter, CamJ will calculate the noise STD based on the kTC
            noise.
        sf_prnu_std (float): relative PRNU standard deviation respect to SF gain. 
            PRNU gain standard deviation = prnu_std * gain. The default value is ``0.001``.
    """
    def __init__(
        self,
        # performance parameters
        pd_capacitance = 100e-15, # [F]
        pd_supply = 1.8, # [V]
        dynamic_sf = False,
        output_vs = 1,  # output voltage swing [V]
        num_transistor = 3,
        enable_cds = False,
        fd_capacitance = 10e-15,  # [F]
        load_capacitance = 1e-12,  # [F]
        tech_node = 130,  # [um]
        pitch = 4,  # [um]
        array_vsize = 128,
        # noise model parameters
        dark_current_noise = 0.,
        enable_dcnu = False,
        enable_prnu = False,
        dcnu_std = 0.001,
        fd_gain = 1.0,
        fd_noise = None,
        fd_prnu_std = 0.001,
        sf_gain = 1.0,
        sf_noise = None,
        sf_prnu_std = 0.001
    ):
        self.name = "ActivePixelSensor"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.OPTICAL]
        self.output_domain = ProcessDomain.VOLTAGE

        # set input/output driver
        self.input_need_driver = False
        self.output_driver = True

        self.enable_cds = enable_cds
        if enable_cds:
            self.num_readout = 2
        else:
            self.num_readout = 1

        self.energy_model = ActivePixelSensorEnergy(
            pd_capacitance = pd_capacitance,
            pd_supply = pd_supply,
            dynamic_sf = dynamic_sf,
            output_vs = output_vs,
            num_transistor = num_transistor,
            fd_capacitance = fd_capacitance,
            num_readout = self.num_readout,
            load_capacitance = load_capacitance,
            tech_node = tech_node,
            pitch = pitch,
            array_vsize = array_vsize
        )

        # calculate thermal noise
        if fd_noise == None:
            fd_noise = _cap_thermal_noise(fd_capacitance)
        if sf_noise == None:
            sf_noise = _single_pole_rc_circuit_thermal_noise(
                num_transistor = 2,
                inversion_level = "strong",
                capacitance = load_capacitance
            )

        self.noise_components = [
            PhotodiodeFunc(
                name = "Photodiode",
                dark_current_noise = dark_current_noise,
                enable_dcnu = enable_dcnu,
                dcnu_std = dcnu_std
            ),
            FloatingDiffusionFunc(
                name = "FloatingDiffusion",
                gain = fd_gain,
                noise = fd_noise,
                enable_cds = enable_cds,
                enable_prnu = enable_prnu,
                prnu_std = fd_prnu_std
            ),
            PixelwiseFunc(
                name = "SourceFollower",
                gain = sf_gain,
                noise = sf_noise,
                enable_prnu = enable_prnu,
                prnu_std = sf_prnu_std,
            )
        ]

    def energy(self):
        """Calculate Energy

        This APS model is a wrapper class for its energy model:
            * ``analog.energy_model.ActivePixelSensorEnergy``.

        Please check out this class for more details.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        return self.energy_model.energy()

    def noise(self, input_signal_list: list):
        """Perform functional simulation

        This function simulates the signal processing behavior inside APS, including signal 
        processing in photodiode, floating diffusion and source follower. Each input signal
        in ``input_signal_list`` will go through each analog componennt functional simulation
        sequentially.

        Please refer to these functions for more detailed descriptions:
            * Photodiode: ``analog.function_model.PhotodiodeFunc``.
            * Floating Diffusion: ``analog.function_model.FloatingDiffusionFunc``.
            * Source Follower: ``analog.function_model.PixelwiseFunc``. 
            
        Args:
            input_signal_list (list): A list of input signals. Each input signal should be a 3D array.

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is the simulated result.
        """
        if not isinstance(input_signal_list, list):
            raise Exception("Input signal to APS needs to be a list of numpy array!")

        return (
            "ActivePixelSensor", 
            default_functional_simulation(self.noise_components, input_signal_list)
        )

# digital pixel sensor
class DigitalPixelSensor(object):
    """Digital Pixel Sensor

    This class models the energy consumption of digital pixel sensor (DPS). This DPS class models
    behavior of a APS and an per-pixel ADC.

    Input/Output domains:
        * input domain: ``ProcessDomain.OPTICAL``.
        * output domain: ``ProcessDomain.DIGITAL``.

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
        enable_cds (bool): enabling CDS or not.
        fd_capacitance (float): [unit: F] the capacitance of FD.
        load_capacitance (float): [unit: F] load capacitance at the SF's output node.
        tech_node (int): [unit: nm] pixel's process node.
        pitch (float): [unit: um] pixel pitch size (width or height).
        array_vsize (int): the vertical size of the entire pixel array. This is used to estimate 
            the parasitic capacitance on the SF's readout wire.
        adc_type (str): the actual ADC type. Please check ADC class for more details.
        adc_fom (float): [unit: J/conversion] ADC's Figure-of-Merit, expressed by energy per conversion.
        adc_resolution (int): ADC's resolution. ``8`` stands for 8-bit digital resolution, [0, 256).
        dark_current_noise (float): average dark current noise in unit of electrons (e-).
        enable_dcnu (bool): flag to enable dark current non-uniformity, the default value is ``False``.
        enable_prnu (bool): flag to enable PRNU. Default value is ``False``.
        dcnu_std (float): dcnu standard deviation percentage. it is relative number respect
            to ``dark_current_noise``, the dcnu standard deviation is,
            ``dcnu_std`` * ``dark_current_noise``, the default value is ``0.001``.
        fd_gain (float): the gain of FD, the default value is ``1.0``.
        fd_noise (float): the stadard deviation of FD read noise, the default value is ``None``. If
            users do not specific this parameter, CamJ will calculate the noise STD based on the kTC
            noise.
        fd_prnu_std (float): relative PRNU standard deviation respect to FD gain. 
            PRNU gain standard deviation = prnu_std * gain. The default value is ``0.001``.
        sf_gain (float): the gain of SF, the default value is ``1.0``.
        sf_noise (float): the stadard deviation of SF read noise, the default value is ``None``. If
            users do not specific this parameter, CamJ will calculate the noise STD based on the kTC
            noise.
        sf_prnu_std (float): relative PRNU standard deviation respect to SF gain. 
            PRNU gain standard deviation = prnu_std * gain. The default value is ``0.001``.
        cds_gain (float): the gain of CDS, the default value is ``1.0``.
        cds_prnu_std (float): relative PRNU standard deviation respect to CDS gain.
            PRNU gain standard deviation = prnu_std * gain. The default value is ``0.001``.
        adc_noise (float): the standard deviation of read noise from ADC. the default value is ``0.``.
    """
    def __init__(
        self,
        # performance parameters
        pd_capacitance = 100e-15, # [F]
        pd_supply = 1.8, # [V]
        dynamic_sf = False, 
        output_vs = 1,  # output voltage swing [V]
        num_transistor = 3,
        enable_cds = False,
        fd_capacitance = 10e-15,  # [F]
        load_capacitance = 1e-12,  # [F]
        tech_node = 130,  # [um]
        pitch = 4,  # [um]
        array_vsize = 128, # pixel array vertical size
        # ADC performance parameters
        adc_type = 'SS',
        adc_fom = 100e-15,  # [J/conversion]
        adc_reso = 8,
        # noise parameters
        dark_current_noise = 0.,
        enable_dcnu = False,
        enable_prnu = False,
        dcnu_std = 0.001,
        # FD parameters
        fd_gain = 1.0,
        fd_noise = None,
        fd_prnu_std = 0.001,
        # SF parameters
        sf_gain = 1.0,
        sf_noise = None,
        sf_prnu_std = 0.001,
        # CDS parameters
        cds_gain = 1.0,
        cds_noise = None,
        cds_prnu_std = 0.001,
        # ADC parameters
        adc_noise = 0.,
    ):
        self.name = "DigitalPixelSensor"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.OPTICAL]
        self.output_domain = ProcessDomain.DIGITAL

        # set input/output driver
        self.input_need_driver = False
        self.output_driver = False

        self.enable_cds = enable_cds
        if enable_cds:
            self.num_readout = 2
        else:
            self.num_readout = 1

        self.energy_model = DigitalPixelSensorEnergy(
            pd_capacitance = pd_capacitance,
            pd_supply = pd_supply,
            dynamic_sf = dynamic_sf,
            output_vs = output_vs,
            num_transistor = num_transistor,
            fd_capacitance = fd_capacitance,
            load_capacitance = load_capacitance,
            num_readout = self.num_readout,
            tech_node = tech_node,
            pitch = pitch,
            array_vsize = array_vsize,
            adc_type = adc_type,
            adc_fom = 100e-15,
            adc_reso = 8
        )

        # calculate thermal noise
        # if enable cds then there is no fd noise, else otherwise.
        if enable_cds:
            fd_noise = 0
        else:
            if fd_noise is None:
                fd_noise = _cap_thermal_noise(fd_capacitance)
        
        if sf_noise is None:
            sf_noise = _single_pole_rc_circuit_thermal_noise(
                num_transistor = 2,
                inversion_level = "strong",
                capacitance = load_capacitance
            )

        self.noise_components = [
            PhotodiodeFunc(
                name = "PhotodiodeFunc",
                dark_current_noise = dark_current_noise,
                enable_dcnu = enable_dcnu,
                dcnu_std = dcnu_std
            ),
            FloatingDiffusionFunc(
                name = "FloatingDiffusion",
                gain = fd_gain,
                noise = fd_noise,
                enable_cds = enable_cds,
                enable_prnu = enable_prnu,
                prnu_std = fd_prnu_std
            ),
            PixelwiseFunc(
                name = "SourceFollower",
                gain = sf_gain,
                noise = sf_noise,
                enable_prnu = enable_prnu,
                prnu_std = sf_prnu_std,
            ),
        ]
        if self.enable_cds:
            self.noise_components.append(
                CorrelatedDoubleSamplingFunc(
                    name = "CorrelatedDoubleSampling",
                    gain = cds_gain,
                    noise = 0.,
                    enable_prnu = enable_prnu,
                    prnu_std = cds_prnu_std
                )
            )
        self.noise_components.append(
            AnalogToDigitalConverterFunc(
                name = "AnalogToDigitalConverter",
                adc_noise = adc_noise,
                max_val = pd_supply,
                resolution = adc_reso,
            )
        )

    def energy(self):
        """Calculate Energy

        To see the details of energy modeling, please check out:
            * ``analog.energy_model.DigitalPixelSensorEnergy``.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        return self.energy_model.energy()

    def noise(self, input_signal_list):
        """Perform functional simulation

        This function simulates the signal processing behavior inside DPS, including signal 
        processing in photodiode, floating diffusion, source follower and ADC. Each input signal
        in ``input_signal_list`` will perform functional simulation sequentially.

        To see the details of function modeling, please refer:
            * Photodiode: ``analog.function_model.PhotodiodeFunc``.
            * Floating Diffusion: ``analog.function_model.FloatingDiffusionFunc``.
            * Source Follower: ``analog.function_model.PixelwiseFunc``.
            * Correlated Double Sampling: ``analog.function_model.CorrelatedDoubleSamplingFunc``.
            * Analog-To-Digital Converter: ``analog.function_model.AnalogToDigitalConverterFunc``.
            
        Args:
            input_signal_list (list): A list of input signals. Each input signal should be a 3D array.

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is the simulated result.
        """
        if not isinstance(input_signal_list, list):
            raise Exception("Input signal to DPS needs to be a list of numpy array!")

        return (
            "DigitalPixelSensor",
            default_functional_simulation(self.noise_components, input_signal_list)
        )

class PulseWidthModulationPixel(object):
    """Pulse-Width-Modulation (PWM) Pixel

    The modeled PWM pixel consists of a photodiode (PD), a ramp signal generator, and a comparator.
    The comparator output toggles when the ramp signal is smaller than the pixel voltage at PD.

    This PWM pixel class **ONLY** supports energy modeling, currently no functional modeling.

    Input/Output domains:
        * input domain: ``ProcessDomain.OPTICAL``.
        * output domain: ``ProcessDomain.TIME``.

    Args:
        pd_capacitance: PD capacitance.
        pd_supply: PD voltage supply.
        array_vsize:, the vertical size of the pixel array. For A ``720x1280`` (H, W) resolution
            pixel array, its vertical size is ``720``.
        ramp_capacitance: the capacitance of ramp signal generator.
        gate_capacitance: the gate capacitance of readout transistor.
        num_readout: number of read from pixel.
    """
    def __init__(
        self,
        pd_capacitance = 100e-15, # [F]
        pd_supply = 1.8, # [V]
        array_vsize = 126, # pixel array vertical size
        ramp_capacitance = 1e-12,  # [F]
        gate_capacitance = 10e-15,  # [F]
        num_readout = 1,
    ):
        self.name = "PulseWidthModulationPixel"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.OPTICAL]
        self.output_domain = ProcessDomain.TIME

        # set input/output driver
        self.input_need_driver = False
        self.output_driver = True

        self.energy_model = PulseWidthModulationPixelEnergy(
            pd_capacitance = pd_capacitance,
            pd_supply = pd_supply,
            array_vsize = array_vsize,
            ramp_capacitance = ramp_capacitance,
            gate_capacitance = gate_capacitance,
            num_readout = num_readout
        )

    def energy(self):
        """Calculate Energy

        For energy modeling, please check out ``analog.energy_model.PulseWidthModulationPixelEnergy``
        for more details.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        return self.energy_model.energy()

    def noise(self, input_signal_list):
        """Perform functional simulation
        
        TODO: (tianrui)

        .. Note::
            Currently, we don't support the functional simulation for PWM pixels, ``input_signal_list``
            will be directly returned ny this function.

        Args:
            input_signal_list (list): A list of input signals. Each input signal should be a 3D array.

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is the simulated result.
        """
        # haven't implemented the noise model for PWM pixel yet.
        return ("PulseWidthModulationPixel", input_signal_list)


class ColumnAmplifier(object):
    """Column Amplifier

    The class models the hardware behavior of a typical column amplifier. It includes an input capacitor,
    a feedback capacitor, a load capacitor, and an amplifier. This amplifier can be used either as 
    pixel array's column amplifier or as a general-purpose switched-capacitor amplifier, such as
    switched-capacitor integrator, switched-capacitor subtractor, and switched-capacitor multiplier.

    Input/Output domains:
        * input domain: ``ProcessDomain.VOLTAGE``.
        * output domain: ``ProcessDomain.VOLTAGE``.

    Args:
        load_capacitance (float): [unit: F] load capacitance.
        input_capacitance (float): [unit: F] input capacitance.
        t_sample (float): [unit: s] sampling time, which mainly consists of the amplifier's 
            settling time.
        t_hold (float): [unit: s] holding time, during which the amplifier is turned on and
            consumes power relentlessly.
        supply (float): [unit: V] supply voltage.
        gain_cl (int): amplifier's closed-loop gain. This gain describes the ratio of 
            ``input_capacitance`` over feedback capacitance.
        differential (bool): if using differential-input amplifier or single-input amplifier.
        gain (float): the average gain. Default value is ``1.0``.
        noise (float): the stadard deviation of read noise, the default value is ``None``. If
            users do not specific this parameter, CamJ will calculate the noise STD based on 
            the kTC noise.
        ennable_prnu (bool): flag to enable PRNU. Default value is ``False``.
        prnu_std (float): the relative PRNU standard deviation respect to gain.
            PRNU gain standard deviation = prnu_std * gain. The default value is ``0.001``.
        enable_offset (bool): flag to enable adding offset voltage. Default value is ``False``.
        pixel_offset_voltage: pixel offset voltage in unit of volt (V). Default value is ``0.1``.
        col_offset_voltage: column-wise offset voltage in unit of volt (V). Default value is ``0.05``.
    """

    def __init__(
        self,
        # performance parameters
        load_capacitance = 1e-12,  # [F]
        input_capacitance = 1e-12,  # [F]
        t_sample = 2e-6,  # [s]
        t_hold = 10e-3,  # [s]
        supply = 1.8,  # [V]
        gain_cl = 2,
        gain_open = 256,
        differential = False,
        # noise parameters
        gain = 1,
        noise = None,
        enable_prnu = False,
        prnu_std = 0.001,
        enable_offset = False,
        pixel_offset_voltage = 0.1,
        col_offset_voltage = 0.05
    ):
        self.name = "ColumnAmplifier"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.VOLTAGE]
        self.output_domain = ProcessDomain.VOLTAGE

        # set input/output driver
        self.input_need_driver = False
        self.output_driver = True

        self.energy_model = ColumnAmplifierEnergy(
            load_capacitance = load_capacitance,
            input_capacitance = input_capacitance,
            t_sample = t_sample,
            t_hold = t_hold,
            supply = supply,
            gain_cl = gain_cl,
            differential = differential
        )

        if noise is None:
            noise = _single_pole_rc_circuit_thermal_noise(
                num_transistor = 8,
                inversion_level = "strong",
                capacitance = load_capacitance
            )

        self.func_model = ColumnwiseFunc(
            name = "ColumnAmplifier",
            gain = gain,
            noise = noise,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std,
            enable_offset = enable_offset,
            pixel_offset_voltage = pixel_offset_voltage,
            col_offset_voltage = col_offset_voltage
        )

    def energy(self):
        """Calculate Energy

        This class supports both energy modeling and functional modeling. The details of energy modeling, please check out:
            * ``analog.energy_model.ColumnAmplifierEnergy``.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        return self.energy_model.energy()

    def noise(self, input_signal_list):
        """Perform functional simulation

        This function simulates the signal processing behavior of column amplifier. Each input signal
        in ``input_signal_list`` will perform functional simulation sequentially.

        To see the details of function modeling, please refer:
            * ``analog.function_model.ColumnwiseFunc``.
            
        Args:
            input_signal_list (list): A list of input signals. Each input signal should be a 3D array.

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is a list of simulation results.
        """
        output_signal_list = []
        for input_signal in input_signal_list:
            if input_signal.ndim == 2:
                raise Exception("Input signal to 'ColumnAmplifier' needs to be 3 dimentional (height, width, channel)")

            output_signal_list.append(
                self.func_model.simulate_output(
                    input_signal
                )
            )
        return (self.func_model.name, output_signal_list)

class SourceFollower(object):
    """Source Follower

    This class models the behavior of source follower. It can be applied to not only the single-transistor
    source follower but also flipped-voltage-follower (FVF).
    
    Input/Output domains:
        * input domain: ``ProcessDomain.VOLTAGE``.
        * output domain: ``ProcessDomain.VOLTAGE``.

    Args:
        load_capacitance (float): [unit: F] load capacitance.
        supply (float): [unit: V] supply voltage.
        output_vs (float): [unit: V] voltage swing at the SF's output node.
        bias_current (float): [unit: A] bias current.
        gain (float): the average gain. Default value is ``1.0``.
        noise (float): the stadard deviation of read noise, the default value is ``None``. If
            users do not specific this parameter, CamJ will calculate the noise STD based on 
            the kTC noise.
        enable_prnu (bool): flag to enable PRNU. Default value is ``False``.
        prnu_std (float): the relative prnu standard deviation respect to gain.
            prnu gain standard deviation = prnu_std * gain. the default value is ``0.001``.
    """

    def __init__(
        self,
        # performance parameters
        load_capacitance = 1e-12,  # [F]
        supply = 1.8,  # [V]
        output_vs = 1,  # [V]
        bias_current = 5e-6,  # [A]
        # noise parameters
        gain = 1.0,
        noise = None,
        enable_prnu = False,
        prnu_std = 0.001,
    ):
        self.name = "SourceFollower"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.VOLTAGE]
        self.output_domain = ProcessDomain.VOLTAGE

        # set input/output driver
        self.input_need_driver = True
        self.output_driver = True

        self.energy_model = SourceFollowerEnergy(
            load_capacitance = load_capacitance,
            supply = supply,
            output_vs = output_vs,
            bias_current = bias_current,
        )

        if noise is None:
            noise = _single_pole_rc_circuit_thermal_noise(
                num_transistor = 4,
                inversion_level = "strong",
                capacitance = load_capacitance
            )

        self.func_model = PixelwiseFunc(
            name = "SourceFollower",
            gain = gain,
            noise = noise,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std
        )

    def energy(self):
        """Calculate Energy

        To see the details of energy modeling, please check out:
            * ``analog.energy_model.SourceFollowerEnergy``.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        return self.energy_model.energy()

    def noise(self, input_signal_list):
        """Perform functional simulation

        Simulate the functional behavior of a source follower. Here, we use a generic functional
        modeling class to model source follower.

        To see the details of function modeling, please refer the pixel-wise generic modeling class:
            * ``analog.function_model.PixelwiseFunc``.

        Args:
            input_signal_list (list): A list of input signals. Each input signal should be a 3D array.

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is a list of simulation results.
        """
        output_signal_list = []
        for input_signal in input_signal_list:
            if input_signal.ndim != 3:
                raise Exception("input signal to 'SourceFollower' needs to be in (height, width, channel) 3D shape.")

            output_signal_list.append(
                self.func_model.simulate_output(
                    input_signal
                )
            )
        return (self.func_model.name, output_signal_list)

class ActiveAnalogMemory(object):
    """Active Analog Memory
    
    This class models the behavior of active analog memory. The model itself consists of a capacitor,
    a compensation capacitor, and an amplifier which holds the stored analog data through feedback.

    Input/Output domains:
        * input domain: ``ProcessDomain.VOLTAGE``.
        * output domain: ``ProcessDomain.VOLTAGE``.

    Args:
        sample_capacitance (float): [unit: F] sample capacitance.
        comp_capacitance (float): [unit: F] compensation capacitance
        t_sample (float): [unit: s] sampling time, which mainly consists of the amplifier's settling time.
        t_hold (float): [unit: s] holding time, during which the amplifier is turned on and consumes
            power relentlessly.
        supply (float): [unit: V] supply voltage.
        noise (float): the stadard deviation of read noise, the default value is ``None``. If
            users do not specific this parameter, CamJ will calculate the noise STD based on 
            the kTC noise.
        enable_prnu (bool): flag to enable PRNU. Default value is ``False``.
        prnu_std (float): the relative prnu standard deviation respect to gain.
                  prnu gain standard deviation = prnu_std * gain.
                  the default value is ``0.001``.
    """

    def __init__(
        self,
        # performance parameters
        sample_capacitance = 2e-12,  # [F]
        comp_capacitance = 2.5e-12,  # [F]
        t_sample = 1e-6,  # [s]
        t_hold = 10e-3,  # [s]
        supply = 1.8,  # [V]
        # noise parameters
        noise = None,
        enable_prnu = False,
        prnu_std = 0.001,
    ):
        self.name = "ActiveAnalogMemory"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.VOLTAGE]
        self.output_domain = ProcessDomain.VOLTAGE

        # set input/output driver
        self.input_need_driver = False
        self.output_driver = True

        # noise from sample (input)
        input_noise = _single_pole_rc_circuit_thermal_noise(
            num_transistor = 8,
            inversion_level = "strong",
            capacitance = comp_capacitance+sample_capacitance
        )

        # noise from hold (output)
        output_noise = _single_pole_rc_circuit_thermal_noise(
            num_transistor = 8,
            inversion_level = "strong",
            capacitance = comp_capacitance
        )
        # set gain to 1
        gain = 1.0
        # because gain is 1 so input and output noise can be added together
        if noise is None:
            noise = input_noise + output_noise

        self.energy_model = ActiveAnalogMemoryEnergy(
            sample_capacitance = sample_capacitance,
            comp_capacitance = comp_capacitance,
            t_sample = t_sample,
            t_hold = t_hold,
            supply = supply
        )

        self.func_model = PixelwiseFunc(
            name = "ActiveAnalogMemory",
            gain = gain,
            noise = noise,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std
        )

    def energy(self):
        """Calculate Energy

        To see the details of energy modeling, please check out:
            * ``analog.energy_model.ActiveAnalogMemoryEnergy``.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        return self.energy_model.energy() 

    def noise(self, input_signal_list):
        """Perform functional simulation

        Simulate the functional behavior of an acitve analog memory. Here, we use a generic functional
        modeling class.

        To see the details of function modeling, please refer:
            * ``analog.function_model.PixelwiseFunc``.

        Args:
            input_signal_list (list): A list of input signals. Each input signal should be a 2D/3D array.

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is a list of simulation results.
        """
        output_signal_list = []
        for input_signal in input_signal_list:
            if input_signal.ndim != 3:
                raise Exception("input signal to 'ActiveAnalogMemory' needs to be in (height, width, channel) 3D shape.")
            output_signal_list.append(
                self.func_model.simulate_output(
                    input_signal
                )
            )
        return (self.func_model.name, output_signal_list)


class PassiveAnalogMemory(object):
    """Passive Analog Memory

    This class models the behavior of passive analog memory. The model only contains a sample capacitor. 
    Compared to active analog memory, it has higher data leakage rate.

    Input/Output domains:
        * input domain: ``ProcessDomain.VOLTAGE``.
        * output domain: ``ProcessDomain.VOLTAGE``.

    Args:
        sample_capacitance (float): [unit: F] sample capacitance.
        supply (float): [unit: V] supply voltage.
        noise (float): the stadard deviation of read noise, the default value is ``None``. If
            users do not specific this parameter, CamJ will calculate the noise STD based on 
            the kTC noise.
        enable_prnu (bool): flag to enable PRNU. Default value is ``False``.
        prnu_std (float): the relative prnu standard deviation respect to gain.
                  prnu gain standard deviation = prnu_std * gain. the default value is ``0.001``.
        
    """
    def __init__(
        self,
        # performance parameters
        sample_capacitance = 1e-12,  # [F]
        supply = 1.8,  # [V]
        # eqv_reso  # equivalent resolution
        # noise parameters
        noise = None,
        enable_prnu = False,
        prnu_std = 0.001,
        
    ):
        self.name = "PassiveAnalogMemory"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.VOLTAGE]
        self.output_domain = ProcessDomain.VOLTAGE

        # set input/output driver
        self.input_need_driver = False
        self.output_driver = False

        self.energy_model = PassiveAnalogMemoryEnergy(
            sample_capacitance = sample_capacitance,
            supply = supply
        )

        if noise is None:
            noise = _cap_thermal_noise(sample_capacitance)
        gain = 1.0

        self.func_model = PixelwiseFunc(
            name = "PassiveAnalogMemory",
            gain = gain,
            noise = noise,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std
        )

    def energy(self):
        """Calculate Energy

        To see the details of energy modeling, please check out:
            * ``analog.energy_model.PassiveAnalogMemoryEnergy``.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        return self.energy_model.energy()

    def noise(self, input_signal_list):
        """Perform functional simulation

        Simulate the functional behavior of an passive analog memory. The functional behavior of
        this component is used a generic noise model.

        To see the details of function modeling, please refer:
            * ``analog.function_model.PixelwiseFunc``.

        Args:
            input_signal_list (list): A list of input signals. Each input signal should be a 2D/3D array.

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is a list of simulation results.
        """
        output_signal_list = []
        for input_signal in input_signal_list:
            if input_signal.ndim != 3:
                raise Exception("input signal to 'PassiveAnalogMemory' needs to be in (height, width, channel) 3D shape.")
            output_signal_list.append(
                self.func_model.simulate_output(
                    input_signal
                )
            )
        return (self.func_model.name, output_signal_list)

class CurrentMirror(object):
    """Current Mirror.

    This class models the behavior of current mirror. The class models a constant current path and
    a load capacitor.

    .. Note::
        This class can perform current duplication or current-time multiplication depending on
        user's definition. When ``i_dc`` is not None, this class will perform current duplication and
        the output signal domain is current. Otherwise, this class performs current-time multiplication
        and accumulate the charges on its own load capacitor. The output signal domain would be voltage.

    Input/Output domains:
        * input domain: ``ProcessDomain.CURRENT`` and ``ProcessDomain.TIME``.
        * output domain: if ``i_dc`` is ``None``, then ``ProcessDomain.VOLTAGE``, else, ``ProcessDomain.CURRENT``.

    Args:
        supply (float): [unit: V] supply voltage.
        load_capacitance (float): [unit: F] load capacitance.
        t_readout (float): [unit: s] readout time, during which the constant current drives
            the load capacitance from 0 to VDD.
        i_dc (float): [unit: A] the constant current. If ``i_dc == None``, then i_dc is
            estimated from the other parameters.
        noise (float): the stadard deviation of read noise, the default value is ``None``. If
            users do not specific this parameter, CamJ will calculate the noise STD based on 
            the kTC noise.
        enable_prnu (bool): flag to enable PRNU. Default value is ``False``.
        prnu_std (float): the relative prnu standard deviation respect to gain.
            prnu gain standard deviation = prnu_std * gain. The default value is ``0.001``.
    """
    def __init__(
        self,
        # performance parameters
        supply = 1.8,
        load_capacitance = 2e-12,  # [F]
        t_readout = 1e-6,  # [s]
        i_dc = 1e-6,  # [A]
        # noise parameters
        noise = None,
        enable_prnu = False,
        prnu_std = 0.001

    ):
        self.name = "CurrentMirror"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.CURRENT, ProcessDomain.TIME]

        # set input/output driver
        self.input_need_driver = True
        self.output_driver = True

        if i_dc is None and noise is None:
            self.output_domain = ProcessDomain.VOLTAGE
            # if output domain is voltage, the noise is the load capacitor's thermal noise.
            noise = _single_pole_rc_circuit_thermal_noise(
                num_transistor = 1,
                inversion_level = "strong",
                capacitance = load_capacitance
            )
            enable_compute = True
        elif i_dc is None and noise is not None:
            self.output_domain = ProcessDomain.CURRENT
            # when the output domain is current, the major noise comes from current mismatch.
            # Here, we can't model directly and we set the noise to be 0. [TODO]
            noise = 0
            enable_compute = False

        gain = 1.0

        self.energy_model = CurrentMirrorEnergy(
            supply = supply,
            load_capacitance = load_capacitance,
            t_readout = t_readout,
            i_dc = i_dc
        )

        self.func_model = CurrentMirrorFunc(
            name = "CurrentMirror",
            gain = gain,
            noise = noise,
            enable_compute = enable_compute,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std
        )

    def energy(self):
        """Calculate Energy

        To see the details of energy modeling, please check out:
            * ``analog.energy_model.CurrentMirrorEnergy``.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        return self.energy_model.energy()

    def noise(self, input_signal_list):
        """Perform functional simulation

        This function simulates the functional behavior of an current mirror.

        .. Note::
            This function accepts two types of inputs. When the length of ``input_signal_list`` is ``1``.
            This function will perform copy operation that directly copy the input signal to the output
            signal with noise simulation. When the length of ``input_signal_list`` is ``2``. This 
            function will perform element-wise multiplication. One input is the time signal and the 
            second one is the current signal.

        To see the details of function modeling, please refer:
            * ``analog.function_model.CurrentMirrorFunc``.

        Args:
            input_signal_list (list): A list of input signals. Each input signal should be a 3D array. The length of ``input_signal_list``  should be either ``1`` or ``2``.

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is a list of simulation results.
        """
        # if input is two signal matrices, current mirror performs element-wise multiplication.
        if len(input_signal_list) == 2:
            return (
                self.func_model.name, 
                [self.func_model.simulate_output(input_signal_list[0], input_signal_list[1])]
            )
        # else just copy data over.
        elif len(input_signal_list) == 1:
            return (
                self.func_model.name, 
                [self.func_model.simulate_output(input_signal_list[0])]
            )
        else:
            raise Exception("Input signal list to 'CurrentMirror' can only be length of 1 or 2!")


class PassiveSwitchedCapacitorArray(object):
    """Passive Switched Capacitor Array

    The model consists of a list of capacitors and a list of voltages that corresponds to 
    the voltage swing at each capacitor. The model is used to represent all passive 
    switched-capacitor computational circuits, including charge-redistribution-based MAC operation.

    .. Note::
        The default behavior of this class is to perform element-wise accumulation. For instance,
        if ``input_signal_list`` is ``[np.array([1, 2, 3]), np.array([1, 2, 3]), np.array([1, 2, 3])]``,
        the output from ``noise`` function is ``np.array([3, 6, 9])``. For achieve functionality of
        convolution, please check out ``analog.component.Voltage2VoltageConv``.

    Input/Output domains:
        * input domain: ``ProcessDomain.VOLTAGE``.
        * output domain: ``ProcessDomain.VOLTAGE``.

    Args:
        capacitance_array (array, float): [unit: F] a list of capacitors.
        vs_array (array, float): [unit: V] a list of voltages that corresponds to the voltage swing
             at each capacitor.
        noise (float): the stadard deviation of read noise, the default value is ``None``. If
            users do not specific this parameter, CamJ will calculate the noise STD based on 
            the kTC noise.
    """
    def __init__(
        self,
        # peformance parameters
        capacitance_array,
        vs_array,
        # noise parameters
        noise = None
    ):
        self.name = "PassiveSwitchedCapacitorArray"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.VOLTAGE]
        self.output_domain = ProcessDomain.VOLTAGE

        # set input/output driver
        self.input_need_driver = False
        self.output_driver = False

        self.energy_model = PassiveSwitchedCapacitorArrayEnergy(
            capacitance_array = capacitance_array,
            vs_array = vs_array
        )
        # because we can't accurately model the compute pattern at this point, we simply 
        # average the capacitance and model the average noise
        if noise is None:
            noise = _cap_thermal_noise(
                capacitance = np.mean(capacitance_array)
            )

        self.func_model = PassiveSwitchedCapacitorArrayFunc(
            name = "PassiveSwitchedCapacitorArray",
            num_capacitor = len(capacitance_array),
            noise = noise
        )

    def energy(self):
        """Calculate Energy

        To see the details of energy modeling, please check out:
            * ``analog.energy_model.PassiveSwitchedCapacitorArrayEnergy``.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        return self.energy_model.energy()

    def noise(self, input_signal_list):
        """Perform functional simulation

        This function simulates the functional behavior of a passive switched capacitor array.

        To see the details of function modeling, please refer:
            * ``analog.function_model.PassiveSwitchedCapacitorArrayFunc``.

        Args:
            input_signal_list (list): A list of input signals. Each input signal should be a 3D array.

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is a list of simulation results.
        """
        # perform element-wise addition across different input signals.
        return (
            self.func_model.name, 
            [self.func_model.simulate_output(input_signal_list)]
        )

class Comparator(object):
    """Dynamic Voltage Comparator

    The class models the behavior of dynamic voltage comparator.

    .. Note::
        The functional simulation of this class is slightly different than the actual analog
        comparator. In the actual comparator, it compares the two different input signals 
        (``In1`` and ``In2``) and output either ``Vdd`` (if ``In1`` >= ``In2``) or ``0`` (if 
        ``In1`` < ``In2``). Here, in order to support other computations, we modified the output
        of the comparator to be ``In1`` (if ``In1`` >= ``In2``) or ``0`` (if ``In1`` < ``In2``).

    Input/Output domains:
        * input domain: ``ProcessDomain.VOLTAGE``.
        * output domain: ``ProcessDomain.VOLTAGE``.

    Args:
        supply (float): [unit: V] supply voltage.
        i_bias (float): [unit: A] bias current of the circuit.
        t_readout (float): [unit: s] readout time, during which the comparison is finished.
        enable_prnu (bool): flag to enable PRNU. Default value is ``False``.
        prnu_std (float): the relative prnu standard deviation respect to gain.
                  prnu gain standard deviation = prnu_std * gain.
                  the default value is ``0.001``.
    """
    def __init__(
        self,
        # performance parameters
        supply = 1.8,  # [V]
        i_bias = 10e-6,  # [A]
        t_readout = 1e-9,  # [s]
        # noise parameters
        enable_prnu = False,
        prnu_std = 0.001
    ):
        self.name = "Comparator"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.VOLTAGE]
        self.output_domain = ProcessDomain.VOLTAGE

        # set input/output driver
        self.input_need_driver = True
        self.output_driver = False

        self.energy_model = ComparatorEnergy(
            supply = supply,
            i_bias = i_bias,
            t_readout = t_readout
        )

        self.func_model = ComparatorFunc(
            name = "Comparator",
            gain = 1,
            noise = 0,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std
        )

    def energy(self):
        """Calculate Energy

        To see the details of energy modeling, please check out:
            * ``analog.energy_model.ComparatorEnergy``.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        return self.energy_model.energy()

    def noise(self, input_signal_list):
        """Perform functional simulation

        This function simulates the functional behavior of a comparator.

        To see the details of function modeling, please refer:
            * ``analog.function_model.ComparatorFunc``.

        Args:
            input_signal_list (list): A list of input signals. The length of this list is 2. Each input signal should be a 3D array.

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is a list of simulation results.
        """
        if len(input_signal_list) == 2:
            return (
                self.func_model.name, 
                [self.func_model.simulate_output(input_signal_list[0], input_signal_list[1])]
            )
        else:
            raise Exception("Input signal list to Comparator can only be length of 2!")


class AnalogToDigitalConverter(object):
    """Analog-to-Digital Converter.

    This class model the behavior of ADC.

    Input/Output domains:
        * input domain: ``ProcessDomain.VOLTAGE``.
        * output domain: ``ProcessDomain.DIGITAL``.

    Args:
        supply (float): [unit: V] supply voltage.
        type (str): ADC type.
        fom (float): [unit: J/conversion] ADC's Figure-of-Merit, expressed by energy per conversion.
        resolution (int): ADC resolution.
        adc_noise (float): ADC noise.
    """

    def __init__(
        self,
        # performance parameters
        supply=1.8,  # [V]
        type='SS',
        fom=100e-15,  # [J/conversion]
        resolution=8,
        # noise parameters
        adc_noise = 0.,
    ):
        self.name = "AnalogToDigitalConverter"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.VOLTAGE]
        self.output_domain = ProcessDomain.DIGITAL

        # set input/output driver
        self.input_need_driver = True
        self.output_driver = False

        self.energy_model = AnalogToDigitalConverterEnergy(
            supply = supply,
            type = type,
            fom = fom,
            resolution = resolution,
        )

        self.func_model = AnalogToDigitalConverterFunc(
            name = "AnalogToDigitalConverter",
            adc_noise = adc_noise,
            max_val = supply,
            resolution = resolution,
        )

    def energy(self):
        """Calculate Energy

        To see the details of energy modeling, please check out:
            * ``analog.energy_model.AnalogToDigitalConverterEnergy``.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        return self.energy_model.energy()

    def noise(self, input_signal_list):
        """Perform functional simulation

        This function simulates the functional behavior of a ADC. The output value range depends on
        the ``resolution`` parameter. For instance, when ``resolution = 8``, the output value range
        is ``[0, 256)``.

        To see the details of function modeling, please refer:
            * ``analog.function_model.AnalogToDigitalConverterFunc``.

        Args:
            input_signal_list (list): A list of input signals. Each input signal should be a 3D array.

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is a list of simulation results.
        """
        output_signal_list = []
        for input_signal in input_signal_list:
            output_signal_list.append(
                self.func_model.simulate_output(
                    input_signal
                )
            )
        return (self.func_model.name, output_signal_list)


class DigitalToCurrentConverter(object):
    """Digital-to-Current Converter

    This class models the behavior of Digital-to-Current Converter. This model consists of a 
    constant current path and a load capacitor.

    Input/Output domains:
        * input domain: ``ProcessDomain.DIGITAL``.
        * output domain: ``ProcessDomain.CURRENT``.

    Args:
        supply (float): [unit: V] supply voltage.
        load_capacitance (float): [unit: F] load capacitance.
        t_readout (float): [unit: s] readout time, during which the constant current drives
            the load capacitance from 0 to VDD.
        gain (float): the average gain. Default value is ``10e-6/256`` in unit of [A/digital number].
            Here, we assume the maximum current is 10 uA and the input digital resolution is 8 bits.
        noise (float): the stadard deviation of read noise, the default value is ``None``. If
            users do not specific this parameter, CamJ will calculate the noise STD based on 
            the kTC noise.
        enable_prnu (bool): flag to enable PRNU. Default value is ``False``.
        prnu_std (float): the relative prnu standard deviation respect to gain.
                  prnu gain standard deviation = prnu_std * gain.
                  the default value is ``0.001``.
    """
    def __init__(
        self,
        # performance parameters
        supply = 1.8,  # [V]
        load_capacitance = 2e-12,  # [F]
        t_readout = 16e-6,  # [s]
        # noise parameters
        gain = 10e-6/256,  # [A/digital number]
        noise = None,
        enable_prnu = False,
        prnu_std = 0.001,
    ):
        self.name = "DigitalToCurrentConverter"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.DIGITAL]
        self.output_domain = ProcessDomain.CURRENT

        # set input/output driver
        self.input_need_driver = True
        self.output_driver = True

        self.energy_model = DigitalToCurrentConverterEnergy(
            supply = supply,
            load_capacitance = load_capacitance,
            t_readout = t_readout,
        )

        if noise is None:
            noise = _single_pole_rc_circuit_thermal_noise(
                num_transistor = 2,
                inversion_level = "strong",
                capacitance = load_capacitance
            )

        self.func_model = PixelwiseFunc(
            name = "DigitalToCurrentConverter",
            gain = gain,
            noise = noise,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std
        )

    def energy(self):
        """Calculate Energy

        To see the details of energy modeling, please check out:
            * ``analog.energy_model.DigitalToCurrentConverterEnergy``.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        return self.energy_model.energy()

    def noise(self, input_signal_list):
        """Perform functional simulation

        This function simulates the functional behavior of a DAC.

        To see the details of function modeling, please refer:
            * ``analog.function_model.PixelwiseFunc``.

        Args:
            input_signal_list (list): A list of input signals. Each input signal should be a 3D array.

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is a list of simulation results.
        """
        output_signal_list = []
        for input_signal in input_signal_list:
            output_signal_list.append(
                self.func_model.simulate_output(
                    input_signal
                )
            )
        return (self.func_model.name, output_signal_list)


class MaximumVoltage(object):
    """Maximum Voltage

    A circuit that outputs the maximum voltage among the input voltages. The output of its ``noise()``
    function takes a list of input signals matrices and compare element-wise across those input signals.
    The return of "noise()" is the maximum value for each element-wise comparison across those input signals.

    For instance:
        two lists as input signals, ``[0, 1, 2, 3]`` and ``[3, 2, 1, 0]`` will output ``[3, 2, 2, 3]``
        as the result.

    Input/Output domains:
        * input domain: ``ProcessDomain.VOLTAGE``.
        * output domain: ``ProcessDomain.VOLTAGE``.
    
    Args:
        supply (float): [unit: V] supply voltage.
        t_hold (float): [unit: s] holding time, during which the circuit is turned on and consumes power relentlessly.
        t_readout (float): [unit: s] readout time, during which the maximum voltage is output.
        load_capacitance (float): [unit: F] load capacitance
        gain (float): open-loop gain of the common-source amplifier.
        noise (float): the stadard deviation of read noise, the default value is ``None``. If
            users do not specific this parameter, CamJ will calculate the noise STD based on 
            the kTC noise.
    """
    def __init__(
        self, 
        supply = 1.8,  # [V]
        t_hold = 30e-3,  # [s]
        t_readout = 1e-6,  # [s]
        load_capacitance = 1e-12,  # [F]
        gain = 10,
        noise = None,
    ):
        self.name = "MaximumVoltage"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.VOLTAGE]
        self.output_domain = ProcessDomain.VOLTAGE

        # set input/output driver
        self.input_need_driver = True
        self.output_driver = True

        self.energy_model = MaximumVoltageEnergy(
            supply = supply,  # [V]
            t_hold = t_hold,  # [s]
            t_readout = t_readout,  # [s]
            load_capacitance = load_capacitance,  # [F]
            gain = gain
        )

        if noise is None:
            noise = _single_pole_rc_circuit_thermal_noise(
                num_transistor = 3,
                inversion_level = "moderate",
                capacitance = load_capacitance
            )

        self.func_model = MaximumVoltageFunc(
            name = "MaximumVoltage",
            noise = noise
        )
        
    def energy(self):
        """Calculate Energy

        To see the details of energy modeling, please check out:
            * ``analog.energy_model.MaximumVoltageEnergy``.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        return self.energy_model.energy()

    def noise(self, input_signal_list):
        """Perform functional simulation

        This function simulates the functional behavior of a maximum voltage. This function takes a
        list of input signals and performs element-wise max comparison. The output of this function
        is a list of signal with length of 1.

        To see the details of function modeling, please refer:
            * ``analog.function_model.MaximumVoltageFunc``.

        Args:
            input_signal_list (list): A list of input signals. Each input signal should be a 3D array.

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is a list of simulation results.
        """
        return (
                self.func_model.name, 
                [self.func_model.simulate_output(input_signal_list)]
            )


class GeneralCircuit(object):
    """A model for general circuits from first principle.

    TODO: Tianrui.

    .. Note::
        This class is just a rough estimation for its energy, no functional simulation is implemented.

    Args:
        supply (float): [unit: V] supply voltage.
        t_operation (float): [unit: s] operation time, during which the circuit completes its particular operation.
        i_dc (float): [unit: A] direct current of the circuit.
    """
    def __init__(
        self, 
        supply = 1.8,  # [V]
        t_operation = 30e-3,  # [s]
        i_dc = 1e-6,  # [s]
    ):
        self.name = "GeneralCircuit"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.VOLTAGE]
        self.output_domain = ProcessDomain.VOLTAGE

        # set input/output driver
        self.input_need_driver = True
        self.output_driver = True
    
        self.energy_model = GeneralCircuitEnergy(
            supply = supply,  # [V]
            i_dc = i_dc,  # [A]
            t_operation = t_operation  # [s]
        )
        
    def energy(self):
        """Calculate Energy

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        return self.energy_model.energy()

    def noise(self, input_signal_list):
        raise Exception("noise function in 'GeneralCircuit' has not been implemented yet!")

class Adder(object):
    """Adder

    This class models the behavior of adder in analog processing. It can be used to model element-wise
    addition for two matrices of analog signals. This class contains one column ampilifer. [TODO:fixed]
    The amplifier first samples one input element to the output then accumulates the other input element to
    the previous input element at the output. 

    This class can be implemented as a pixel-wise component (each pixel contains an adder) or a column-wise
    component (one-dimensional array to perform addition for all 2D pixel array).

    For instance:
        two lists as input signals, ``[0, 1, 2, 3]`` and ``[3, 2, 1, 0]`` will output ``[3, 3, 3, 3]``
        as the result.

    To see the details of function modeling, please refer its function ``noise()``.

    Input/Output domains:
        * input domain: ``ProcessDomain.VOLTAGE``.
        * output domain: ``ProcessDomain.VOLTAGE``.

    Args:
        load_capacitance (float): [unit: F] load capacitance.
        input_capacitance (float): [unit: F] input capacitance.
        t_sample (float): [unit: s] sampling time, which mainly consists of the amplifier's 
            settling time.
        t_hold (float): [unit: s] holding time, during which the amplifier is turned on and
            consumes power relentlessly.
        supply (float): [unit: V] supply voltage.
        gain_cl (int): amplifier's closed-loop gain. This gain describes the ratio of 
            ``input_capacitance`` over feedback capacitance.
        differential (bool): if using differential-input amplifier or single-input amplifier.
        columnwise_op (bool): flag to set if this operation is column-wise or not. This flag
            will affect the PRNU.
        noise (float): the stadard deviation of read noise, the default value is ``None``. If
            users do not specific this parameter, CamJ will calculate the noise STD based on 
            the kTC noise.
        ennable_prnu (bool): flag to enable PRNU. Default value is ``False``.
        prnu_std (float): the relative PRNU standard deviation respect to gain.
            PRNU gain standard deviation = prnu_std * gain. The default value is ``0.001``.
    """
    def __init__(
        self,
        # performance parameters
        load_capacitance = 1e-12,  # [F]
        input_capacitance = 1e-12,  # [F]
        t_sample = 2e-6,  # [s]
        t_hold = 10e-3,  # [s]
        supply = 1.8,  # [V]
        gain_cl = 1.0,
        differential = False,
        # noise parameters
        columnwise_op = True,
        noise = None,
        enable_prnu = False,
        prnu_std = 0.001
    ):
        self.name = "Adder"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.VOLTAGE]
        self.output_domain = ProcessDomain.VOLTAGE

        # set input/output driver
        self.input_need_driver = False
        self.output_driver = True

        self.energy_model = ColumnAmplifierEnergy(
            load_capacitance = load_capacitance,
            input_capacitance = input_capacitance,
            t_sample = t_sample,
            t_hold = t_hold,
            supply = supply,
            gain_cl = gain_cl,
            differential = differential
        )

        if noise is None:
            noise = _single_pole_rc_circuit_thermal_noise(
                num_transistor = 8,
                inversion_level = "strong",
                capacitance = load_capacitance
            )

        if columnwise_op:
            self.func_model = ColumnwiseFunc(
                name = "ColumnAmplifier",
                gain = 1.0,    # adder no need to amplify the signal
                noise = noise,
                enable_prnu = enable_prnu,
                prnu_std = prnu_std
            )
        else:
            self.func_model = PixelwiseFunc(
                name = "Amplifier",
                gain = 1.0,    # adder no need to amplify the signal
                noise = noise,
                enable_prnu = enable_prnu,
                prnu_std = prnu_std
            )

    def energy(self):
        """Calculate Energy

        To see the details of energy modeling, please check out:
            * ``analog.energy_model.ColumnAmplifierEnergy``.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        # here multiply by 2, because two input signal go through column amplifier
        return self.energy_model.energy() * 2 

    def noise(self, input_signal_list):
        """Perform functional simulation

        This function simulates the functional behavior of an adder. This function takes two input 
        signals and adds them together element-wise. Because we implement this adder using amplifier,
        the input signals are first read by amplifiers and then add together. Here, we model this behavior
        by first simulating the noise effects on these two inputs and then adding the noising outputs
        (out of the amplifier) together.

        Args:
            input_signal_list (list): A list of input signals. The length of this list of 2. 
                Each input signal should be a 3D array.

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is a list of simulation results.
        """
        if len(input_signal_list) == 2:
            if input_signal_list[0].shape != input_signal_list[1].shape:
                raise Exception("Two inputs to 'Adder' need to be in the same shape.")
            noise_input1 = self.func_model.simulate_output(input_signal_list[0])
            noise_input2 = self.func_model.simulate_output(input_signal_list[1])
            return (
                "Adder", 
                [noise_input1 + noise_input2]
            )
        else:
            raise Exception("Input signal list to Comparator can only be length of 2!")


class Subtractor(object):
    """Subtractor

    This class models the behavior of subtractor in analog processing. It can be used to model element-wise
    subtraction for two matrices of analog signals. This class contains one column ampilifer.
    The amplifier first samples one input element to the output then subtracts the other input element from
    the previous input element at the output. 

    This class can be implemented as a pixel-wise component (each pixel contains an sub) or a column-wise
    component (one-dimensional array to perform subtraction for all 2D pixel array).

    For instance:
        two lists as input signals, ``[0, 1, 2, 3]`` and ``[3, 2, 1, 0]`` will output ``[-3, -1, 1, 3]``
        as the result.

    To see the details of function modeling, please refer its function ``noise()``.

    Input/Output domains:
        * input domain: ``ProcessDomain.VOLTAGE``.
        * output domain: ``ProcessDomain.VOLTAGE``.

    Args:
        load_capacitance (float): [unit: F] load capacitance.
        input_capacitance (float): [unit: F] input capacitance.
        t_sample (float): [unit: s] sampling time, which mainly consists of the amplifier's 
            settling time.
        t_hold (float): [unit: s] holding time, during which the amplifier is turned on and
            consumes power relentlessly.
        supply (float): [unit: V] supply voltage.
        gain_cl (int): amplifier's closed-loop gain. This gain describes the ratio of 
            ``input_capacitance`` over feedback capacitance.
        differential (bool): if using differential-input amplifier or single-input amplifier.
        noise (float): the stadard deviation of read noise, the default value is ``None``. If
            users do not specific this parameter, CamJ will calculate the noise STD based on 
            the kTC noise.
        ennable_prnu (bool): flag to enable PRNU. Default value is ``False``.
        prnu_std (float): the relative PRNU standard deviation respect to gain.
            PRNU gain standard deviation = prnu_std * gain. The default value is ``0.001``.
    """
    def __init__(
        self,
        # performance parameters
        load_capacitance = 1e-12,  # [F]
        input_capacitance = 1e-12,  # [F]
        t_sample = 2e-6,  # [s]
        t_hold = 10e-3,  # [s]
        supply = 1.8,  # [V]
        gain_cl = 1.0,
        differential = False,
        # noise parameters
        columnwise_op = True,
        noise = None,
        enable_prnu = False,
        prnu_std = 0.001
    ):
        self.name = "Subtractor"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.VOLTAGE]
        self.output_domain = ProcessDomain.VOLTAGE

        # set input/output driver
        self.input_need_driver = False
        self.output_driver = True

        self.energy_model = ColumnAmplifierEnergy(
            load_capacitance = load_capacitance,
            input_capacitance = input_capacitance,
            t_sample = t_sample,
            t_hold = t_hold,
            supply = supply,
            gain_cl = gain_cl,
            differential = differential
        )

        if noise is None:
            noise = _single_pole_rc_circuit_thermal_noise(
                num_transistor = 8,
                inversion_level = "strong",
                capacitance = load_capacitance
            )

        if columnwise_op:
            self.func_model = ColumnwiseFunc(
                name = "ColumnAmplifier",
                gain = 1.0,    # adder no need to amplify the signal
                noise = noise,
                enable_prnu = enable_prnu,
                prnu_std = prnu_std
            )
        else:
            self.func_model = PixelwiseFunc(
                name = "Amplifier",
                gain = 1.0,    # adder no need to amplify the signal
                noise = noise,
                enable_prnu = enable_prnu,
                prnu_std = prnu_std
            )

    def energy(self):
        """Calculate Energy

        To see the details of energy modeling, please check out:
            * ``analog.energy_model.ColumnAmplifierEnergy``.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        # here multiply by 2, because two input signal go through column amplifier
        return self.energy_model.energy() * 2 

    def noise(self, input_signal_list):
        """Perform functional simulation

        This function simulates the functional behavior of an subtractor. This function takes two input 
        signals (``In1`` and ``In2``) and subtract ``In2`` from ``In1`` element-wise.

        Args:
            input_signal_list (list): A list of input signals. The length of this list of 2. 
                Each input signal should be a 3D array.

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is a list of simulation results.
        """
        if len(input_signal_list) == 2:
            if input_signal_list[0].shape != input_signal_list[1].shape:
                raise Exception("Two inputs to 'Adder' need to be in the same shape.")

            noise_input1 = self.func_model.simulate_output(input_signal_list[0])
            noise_input2 = self.func_model.simulate_output(input_signal_list[1])
            return (
                "Subtractor", 
                [noise_input1 - noise_input2]
            )
        else:
            raise Exception("Input signal list to Comparator can only be length of 2!")


class AbsoluteDifference(object):
    """Absolute Difference

    This class models the behavior of absolution difference in analog processing. It can be used to 
    model element-wise subtraction for two matrices of analog signals. This class contains one comparator and
    one column ampilifer.

    The comparator determines which input element is larger. The amplifier first samples the larger 
    input element to the output then subtracts the smaller input element from the larger input 
    element at the output. Note that the digital logic that determines the amplifier's sampling 
    order based on the comparator's output is ignored. 

    This class can be implemented as a pixel-wise component (each pixel contains an abs) or a column-wise
    component (one-dimensional array to perform absolute difference for all 2D pixel array).

    For instance:
        two lists as input signals, ``[0, 1, 2, 3]`` and ``[3, 2, 1, 0]`` will output ``[3, 1, 1, 3]``
        as the result.

    To see the details of function modeling, please refer its function ``noise()``.

    Input/Output domains:
        * input domain: ``ProcessDomain.VOLTAGE``.
        * output domain: ``ProcessDomain.VOLTAGE``.

    Args:
        load_capacitance (float): [unit: F] load capacitance.
        input_capacitance (float): [unit: F] input capacitance.
        t_sample (float): [unit: s] sampling time, which mainly consists of the amplifier's 
            settling time.
        t_hold (float): [unit: s] holding time, during which the amplifier is turned on and
            consumes power relentlessly.
        supply (float): [unit: V] supply voltage.
        gain_cl (int): amplifier's closed-loop gain. This gain describes the ratio of 
            ``input_capacitance`` over feedback capacitance.
        differential (bool): if using differential-input amplifier or single-input amplifier.
        noise (float): the stadard deviation of read noise, the default value is ``None``. If
            users do not specific this parameter, CamJ will calculate the noise STD based on 
            the kTC noise.
        ennable_prnu (bool): flag to enable PRNU. Default value is ``False``.
        prnu_std (float): the relative PRNU standard deviation respect to gain.
            PRNU gain standard deviation = prnu_std * gain. The default value is ``0.001``.
    """
    def __init__(
        self,
        # performance parameters
        load_capacitance = 1e-12,  # [F]
        input_capacitance = 1e-12,  # [F]
        t_sample = 2e-6,  # [s]
        t_hold = 10e-3,  # [s]
        supply = 1.8,  # [V]
        gain_cl = 1.0,
        differential = False,
        # noise parameters
        noise = None,
        enable_prnu = False,
        prnu_std = 0.001
    ):
        self.name = "AbsoluteDifference"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.VOLTAGE]
        self.output_domain = ProcessDomain.VOLTAGE

        # set input/output driver
        self.input_need_driver = False
        self.output_driver = True        

        self.energy_model = ColumnAmplifierEnergy(
            load_capacitance = load_capacitance,
            input_capacitance = input_capacitance,
            t_sample = t_sample,
            t_hold = t_hold,
            supply = supply,
            gain_cl = gain_cl,
            differential = differential
        )

        if noise is None:
            noise = _single_pole_rc_circuit_thermal_noise(
                num_transistor = 8,
                inversion_level = "strong",
                capacitance = load_capacitance
            )

        self.func_model = AbsoluteDifferenceFunc(
            name = "AbsoluteDifference",
            gain = 1.0,    # adder no need to amplify the signal
            noise = noise,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std
        )

    def energy(self):
        """Calculate Energy

        To see the details of energy modeling, please check out:
            * ``analog.energy_model.ColumnAmplifierEnergy``.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        # here multiply by 2, because two input signal go through column amplifier
        return self.energy_model.energy() * 2 

    def noise(self, input_signal_list):
        """Perform functional simulation

        This function simulates the functional behavior of an absolute difference. This function
        takes two input signals and performs absolute difference element-wise.

        Args:
            input_signal_list (list): A list of input signals. The length of this list of 2. Each input signal should be a 3D array.

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is a list of simulation results.
        """
        if len(input_signal_list) == 2:
            return (
                self.func_model.name, 
                [   
                    self.func_model.simulate_output(
                        input_signal_list[0], 
                        input_signal_list[1]
                    )
                ]
            )
        else:
            raise Exception("Input signal list to Comparator can only be length of 2!")


class MaxPool(object):
    """Max Pooling

    This class performs max pooling in analog processing. The model consists of a constant current path,
    a group of common-source amplifiers, and a load capacitor.

    Based on the mapping software stage, it will perform max pooling with the given kernel size.

    For instance:
        If the input signal is a 2D matrix, ``[[1, 1], [2, 3]]``, a ``2x2`` max pooling will output
        ``[[3]]`` as the result.

    Input/Output domains:
        * input domain: ``ProcessDomain.VOLTAGE``.
        * output domain: ``ProcessDomain.VOLTAGE``.

    Args:
        supply (float): [unit: V] supply voltage.
        t_hold (float): [unit: s] holding time, during which the circuit is turned on and consumes power relentlessly.
        t_readout (float): [unit: s] readout time, during which the maximum voltage is output.
        load_capacitance (float): [unit: F] load capacitance
        gain (float): open-loop gain of the common-source amplifier.
        noise (float): the stadard deviation of read noise, the default value is ``None``. If
            users do not specific this parameter, CamJ will calculate the noise STD based on 
            the kTC noise.
    """
    def __init__(
        self,
        # performance parameters
        supply = 1.8,  # [V]
        t_hold = 30e-3,  # [s]
        t_readout = 1e-6,  # [s]
        load_capacitance = 1e-12,  # [F]
        gain = 10,
        # noise parameters
        noise = None
    ):
        self.name = "MaxPool"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.VOLTAGE]
        self.output_domain = ProcessDomain.VOLTAGE

        # set input/output driver
        self.input_need_driver = False
        self.output_driver = True

        self.kernel_size = None

        self.energy_model = MaximumVoltageEnergy(
            supply = supply,  # [V]
            t_hold = t_hold,  # [s]
            t_readout = t_readout,  # [s]
            load_capacitance = load_capacitance,  # [F]
            gain = gain
        )

        if noise is None:
            noise = _single_pole_rc_circuit_thermal_noise(
                num_transistor = 3,
                inversion_level = "moderate",
                capacitance = load_capacitance
            )

        self.func_model = MaximumVoltageFunc(
            name = "MaximumVoltage",
            noise = noise
        )

    def _set_binning_config(self, kernel_size):
        if len(kernel_size) != 1:
            raise Exception("The length of kernel_size, num_kernels and stride should be 1.")

        if kernel_size[0][-1] != 1:
            raise Exception("'PassiveBinning' only support kernel channel size of 1.")

        self.kernel_size = kernel_size[0][:2]
        
    def energy(self):
        """Calculate Energy

        Here, we use some functionalities of ``analog.energy_model.MaximumVoltageEnergy`` to model
        the energy of this class.

        To see the details of energy modeling, please check out:
            * ``analog.energy_model.MaximumVoltageEnergy``.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        if self.kernel_size is None:
            raise Exception("kernel_size in 'MaxPool' hasn't not been initialized yet!")

        return self.energy_model.energy() * self.kernel_size[0] * self.kernel_size[1]

    def noise(self, input_signal_list):
        """Perform functional simulation

        This function simulates the functional behavior of an max pooling.

        Here, we use some functionalities of ``analog.energy_model.MaximumVoltageFunc`` to model
        the noise simulation of this class.

        To see the details of function modeling, please refer:
            * ``analog.function_model.MaximumVoltageFunc``.

        Args:
            input_signal_list (list): A list of input signals. Each input signal should be a 3D array.

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is a list of simulation results.
        """
        output_signal_list = []
        for input_signal in input_signal_list:
            input_shape = input_signal.shape
            if len(input_shape) != 3:
                raise Exception("'MaxPool' only support 3D input.")
            new_input_shape = (
                input_shape[0] // self.kernel_size[0],
                self.kernel_size[0],
                input_shape[1] // self.kernel_size[1],
                self.kernel_size[1],
                input_shape[2]
            )
            transposed_input_signal = np.transpose(
                input_signal.reshape(new_input_shape),
                (0, 2, 1, 3, 4)
            ).reshape(
                (
                    new_input_shape[0],
                    new_input_shape[2],
                    new_input_shape[1] * new_input_shape[3],
                    new_input_shape[4]
                )
            )

            reshaped_signal_list = []
            for i in range(new_input_shape[1] * new_input_shape[3]):
                reshaped_signal_list.append(transposed_input_signal[:, :, i, :])
            
            output_signal_list.append(
                self.func_model.simulate_output(reshaped_signal_list)
            )

        return ("MaxPool", output_signal_list)


class PassiveAverage(object):
    """Passive Average

    The class performs element-wise average. It uses passive switched capacitor array to realize
    the functionality of averaging (charge redistribution) and uses source followers for signal readout.

    For instance:
        if two input signals, ``[1, 2, 3]`` and ``[3, 4, 5]``, are used as input in ``noise()`` function,
        the expected output signals will be ``[2, 3, 4]``.

    Input/Output domains:
        * input domain: ``ProcessDomain.VOLTAGE``.
        * output domain: ``ProcessDomain.VOLTAGE``.

    Args:
        capacitance_array (array, float): [unit: F] a list of capacitors.
        vs_array (array, float): [unit: V] a list of voltages that corresponds to the voltage swing at each capacitor.
        sf_load_capacitance (float): [unit: F] load capacitance.
        sf_supply (float): [unit: V] supply voltage.
        sf_output_vs (float): [unit: V] voltage swing at the SF's output node.
        sf_bias_current (float): [unit: A] bias current.
        psca_noise (float): the stadard deviation of passive switched capacitor array's read noise,
            the default value is ``None``. If users do not specific this parameter, CamJ will 
            calculate the noise STD based on the kTC noise.
        sf_noise (float): the stadard deviation of SF read noise, the default value is ``None``. If
            users do not specific this parameter, CamJ will calculate the noise STD based on 
            the kTC noise.
        sf_enable_prnu (bool): flag to enable SF PRNU. Default value is ``False``.
        sf_prnu_std (float): the relative prnu standard deviation respect to SF gain.
                  prnu gain standard deviation = prnu_std * gain. the default value is ``0.001``.
    """
    def __init__(
        self,
        # peformance parameters
        capacitance_array,
        vs_array,
        sf_load_capacitance = 1e-12,  # [F]
        sf_supply = 1.8,  # [V]
        sf_output_vs = 1,  # [V]
        sf_bias_current = 5e-6,  # [A]
        # noise parameters
        psca_noise = None,
        sf_noise = None,
        sf_enable_prnu = False,
        sf_prnu_std = 0.001,
        
    ):
        self.name = "PassiveAverage"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.VOLTAGE]
        self.output_domain = ProcessDomain.VOLTAGE

        # set input/output driver
        self.input_need_driver = False
        self.output_driver = True

        self.psca_energy_model = PassiveSwitchedCapacitorArrayEnergy(
            capacitance_array = capacitance_array,
            vs_array = vs_array
        )

        self.sf_energy_model = SourceFollowerEnergy(
            load_capacitance = sf_load_capacitance,
            supply = sf_supply,
            output_vs = sf_output_vs,
            bias_current = sf_bias_current,
        )

        # here, we approximate the noise from PSCA.
        if psca_noise is None:
            psca_noise = _cap_thermal_noise(
                capacitance = np.mean(capacitance_array)
            )

        if sf_noise is None:
            sf_noise = _single_pole_rc_circuit_thermal_noise(
                num_transistor = 2,
                inversion_level = "strong",
                capacitance = sf_load_capacitance
            )
        # set sf gain
        sf_gain = 1.0

        self.psca_func_model = PassiveSwitchedCapacitorArrayFunc(
            name = "PassiveSwitchedCapacitorArray",
            num_capacitor = len(capacitance_array),
            noise = psca_noise
        )

        self.sf_func_model = PixelwiseFunc(
            name = "SourceFollower",
            gain = sf_gain,
            noise = sf_noise,
            enable_prnu = sf_enable_prnu,
            prnu_std = sf_prnu_std
        )

    def energy(self):
        """Calculate Energy

        Passive average inherits some of the functionalities of the energy class below.

        To see the details of energy modeling, please check out:
            * ``analog.energy_model.PassiveSwitchedCapacitorArrayEnergy``.
            * ``analog.energy_model.SourceFollowerEnergy``.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        return self.psca_energy_model.energy() + self.sf_energy_model.energy()

    def noise(self, input_signal_list):
        """Perform functional simulation

        This function simulates the functional behavior of an averaging.

        To see the details of function modeling, please refer:
            * ``analog.function_model.PassiveSwitchedCapacitorArrayFunc``.
            * ``analog.function_model.PixelwiseFunc``.

        Args:
            input_signal_list (list): A list of input signals. Each input signal should be a 3D array.

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is a list of simulation results.
        """
        return (
            "PassiveAverage", 
            [
                self.sf_func_model.simulate_output(
                    self.psca_func_model.simulate_output(
                        input_signal_list
                    )                
                )
            ]
        )

class PassiveBinning(object):
    """Passive Binning

    The class performs binning operations. It uses passive switched capacitor array to realize
    the functionality of binning (via charge redistribution) and uses source followers for signal readout.

    The binning kernel size and stride are determined by the mapped software stage.

    For instance:
        if ``[[1, 2], [3, 4]]`` is used as input for a ``2x2`` binning, the expected output signals
        will be ``[2.5]``.

    Input/Output domains:
        * input domain: ``ProcessDomain.VOLTAGE``.
        * output domain: ``ProcessDomain.VOLTAGE``.

    Args:
        capacitance_array (array, float): [unit: F] a list of capacitors.
        vs_array (array, float): [unit: V] a list of voltages that corresponds to the voltage swing at each capacitor.
        sf_load_capacitance (float): [unit: F] load capacitance.
        sf_supply (float): [unit: V] supply voltage.
        sf_output_vs (float): [unit: V] voltage swing at the SF's output node.
        sf_bias_current (float): [unit: A] bias current.
        psca_noise (float): the stadard deviation of passive switched capacitor array's read noise,
            the default value is ``None``. If users do not specific this parameter, CamJ will 
            calculate the noise STD based on the kTC noise.
        sf_noise (float): the stadard deviation of SF read noise, the default value is ``None``. If
            users do not specific this parameter, CamJ will calculate the noise STD based on 
            the kTC noise.
        sf_enable_prnu (bool): flag to enable SF PRNU. Default value is ``False``.
        sf_prnu_std (float): the relative prnu standard deviation respect to SF gain.
                  prnu gain standard deviation = prnu_std * gain. the default value is ``0.001``.
    """
    def __init__(
        self,
        # peformance parameters
        capacitance_array,
        vs_array,
        sf_load_capacitance = 1e-12,  # [F]
        sf_supply = 1.8,  # [V]
        sf_output_vs = 1,  # [V]
        sf_bias_current = 5e-6,  # [A]
        # noise parameters
        psca_noise = None,
        sf_noise = None,
        sf_enable_prnu = False,
        sf_prnu_std = 0.001,
        
    ):
        self.name = "PassiveBinning"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.VOLTAGE]
        self.output_domain = ProcessDomain.VOLTAGE

        # set input/output driver
        self.input_need_driver = False
        self.output_driver = True

        self.kernel_size = None
        self.psca_energy_model = PassiveSwitchedCapacitorArrayEnergy(
            capacitance_array = capacitance_array,
            vs_array = vs_array
        )

        self.sf_energy_model = SourceFollowerEnergy(
            load_capacitance = sf_load_capacitance,
            supply = sf_supply,
            output_vs = sf_output_vs,
            bias_current = sf_bias_current,
        )

        # here, we approximate the noise from PSCA.
        if psca_noise is None:
            psca_noise = _cap_thermal_noise(
                capacitance = np.mean(capacitance_array)
            )

        if sf_noise is None:
            sf_noise = _single_pole_rc_circuit_thermal_noise(
                num_transistor = 2,
                inversion_level = "strong",
                capacitance = sf_load_capacitance
            )
        # set sf gain
        sf_gain = 1.0

        self.psca_func_model = PassiveSwitchedCapacitorArrayFunc(
            name = "PassiveSwitchedCapacitorArray",
            num_capacitor = len(capacitance_array),
            noise = psca_noise
        )

        self.sf_func_model = PixelwiseFunc(
            name = "SourceFollower",
            gain = sf_gain,
            noise = sf_noise,
            enable_prnu = sf_enable_prnu,
            prnu_std = sf_prnu_std
        )

    def _set_binning_config(self, kernel_size):
        if len(kernel_size) != 1:
            raise Exception("The length of kernel_size, num_kernels and stride should be 1.")

        if kernel_size[0][-1] != 1:
            raise Exception("'PassiveBinning' only support kernel channel size of 1.")

        self.kernel_size = kernel_size[0][:2]

    def energy(self):
        """Calculate Energy

        To see the details of energy modeling, please check out:
            * ``analog.energy_model.PassiveSwitchedCapacitorArrayEnergy``.
            * ``analog.energy_model.SourceFollowerEnergy``.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        return self.psca_energy_model.energy() + self.sf_energy_model.energy()

    def noise(self, input_signal_list):
        """Perform functional simulation

        This function simulates the functional behavior of binning.

        To see the details of function modeling, please refer:
            * ``analog.function_model.PassiveSwitchedCapacitorArrayFunc``.
            * ``analog.function_model.PixelwiseFunc``.

        Args:
            input_signal_list (list): A list of input signals. Each input signal should be a 3D array.

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is a list of simulation results.
        """
        output_signal_list = []
        for input_signal in input_signal_list:
            input_shape = input_signal.shape
            if len(input_shape) != 3:
                raise Exception("'PassiveBinning' only support 3D input.")
            new_input_shape = (
                input_shape[0] // self.kernel_size[0],
                self.kernel_size[0],
                input_shape[1] // self.kernel_size[1],
                self.kernel_size[1],
                input_shape[2]
            )
            transposed_input_signal = np.transpose(
                input_signal.reshape(new_input_shape), 
                (0, 2, 1, 3, 4)
            ).reshape(
                (
                    new_input_shape[0],
                    new_input_shape[2],
                    new_input_shape[1] * new_input_shape[3],
                    new_input_shape[4]
                )
            )

            psca_input_list = []
            for i in range(new_input_shape[1] * new_input_shape[3]):
                psca_input_list.append(
                    transposed_input_signal[:, :, i, :]
                )

            output_signal_list.append(
                self.sf_func_model.simulate_output(
                    self.psca_func_model.simulate_output(
                        psca_input_list
                    )
                )
            )
        return ("PassiveBinning", output_signal_list)


class ActiveAverage(object):
    """Active Average

    The class performs element-wise average. It is implemented by two column amplifiers. [TODO:fixed].
    The two amplifiers first transfer the two input elements to two load capacitors, respectively, then the
    two capacitors are connected together for charge-redistribution.

    For instance:
        if two input signals, ``[1, 2, 3]`` and ``[3, 4, 5]``, are used as input in ``noise()`` function,
        the expected output signals will be ``[2, 3, 4]``.

    Input/Output domains:
        * input domain: ``ProcessDomain.VOLTAGE``.
        * output domain: ``ProcessDomain.VOLTAGE``.

    Args:
        load_capacitance (float): [unit: F] load capacitance.
        input_capacitance (float): [unit: F] input capacitance.
        t_sample (float): [unit: s] sampling time, which mainly consists of the amplifier's 
            settling time.
        t_hold (float): [unit: s] holding time, during which the amplifier is turned on and
            consumes power relentlessly.
        supply (float): [unit: V] supply voltage.
        gain_cl (int): amplifier's closed-loop gain. This gain describes the ratio of 
            ``input_capacitance`` over feedback capacitance.
        differential (bool): if using differential-input amplifier or single-input amplifier.
        noise (float): the stadard deviation of read noise, the default value is ``None``. If
            users do not specific this parameter, CamJ will calculate the noise STD based on 
            the kTC noise.
        ennable_prnu (bool): flag to enable PRNU. Default value is ``False``.
        prnu_std (float): the relative PRNU standard deviation respect to gain.
            PRNU gain standard deviation = prnu_std * gain. The default value is ``0.001``.
        enable_offset (bool): flag to enable adding offset voltage. Default value is ``False``.
        pixel_offset_voltage: pixel offset voltage in unit of volt (V). Default value is ``0.1``.
        col_offset_voltage: column-wise offset voltage in unit of volt (V). Default value is ``0.05``.
    """
    def __init__(
        self,
        # performance parameters
        load_capacitance = 1e-12,  # [F]
        input_capacitance = 1e-12,  # [F]
        t_sample = 2e-6,  # [s]
        t_hold = 10e-3,  # [s]
        supply = 1.8,  # [V]
        gain_cl = 1,
        differential = False,
        # noise parameters
        noise = None,
        enable_prnu = False,
        prnu_std = 0.001,
        enable_offset = False,
        pixel_offset_voltage = 0.1,
        col_offset_voltage = 0.05
    ):
        self.name = "ActiveAverage"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.VOLTAGE]
        self.output_domain = ProcessDomain.VOLTAGE

        # set input/output driver
        self.input_need_driver = True
        self.output_driver = False

        self.energy_model = ColumnAmplifierEnergy(
            load_capacitance = load_capacitance,
            input_capacitance = input_capacitance,
            t_sample = t_sample,
            t_hold = t_hold,
            supply = supply,
            gain_cl = gain_cl,
            differential = differential
        )

        if noise is None:
            noise = _single_pole_rc_circuit_thermal_noise(
                num_transistor = 8,
                inversion_level = "strong",
                capacitance = load_capacitance
            )
        gain = 1.0

        self.func_model = ColumnwiseFunc(
            name = "ColumnAmplifier",
            gain = gain,
            noise = noise,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std
        )

    def _set_binning_config(self, kernel_size):
        if len(kernel_size) != 1:
            raise Exception("The length of kernel_size, num_kernels and stride should be 1.")

        if kernel_size[0][-1] != 1:
            raise Exception("'PassiveBinning' only support kernel channel size of 1.")

        self.kernel_size = kernel_size[0][:2]

    def energy(self):
        """Calculate Energy

        To see the details of energy modeling, please check out:
            * ``analog.energy_model.ColumnAmplifierEnergy``.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        return self.energy_model.energy() * self.kernel_size[0] * self.kernel_size[1]

    def noise(self, input_signal_list):
        """Perform functional simulation

        This function simulates the functional behavior of averaging.

        To see the details of function modeling, please refer:
            * ``analog.function_model.ColumnwiseFunc``.

        Args:
            input_signal_list (list): A list of input signals. Each input signal should be a 3D array.

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is a list of simulation results.
        """
        output_signal_list = []
        for input_signal in input_signal_list:
            output_signal_list.append(
                self.func_model.simulate_output(
                    input_signal
                )
            )

        output_signal_sum = np.zeros(output_signal_list[0].shape)
        for output_signal in output_signal_list:
            output_signal_sum += output_signal

        return ["ActiveAverage", output_signal_sum / len(output_signal_list)]


class ActiveBinning(object):
    """Active Binning

    The class performs binning operations. It is implemented by one column amplifier.
    The amplifier transfers the input elements sequentially to its load capacitor, and the transferred inputs are
    averaged at the capacitor by charge-redistribution.

    The binning kernel size and stride are determined by the mapped software stage.

    For instance:
        if ``[[1, 2], [3, 4]]`` is used as input for a ``2x2`` binning, the expected output signals
        will be ``[2.5]``.

    Input/Output domains:
        * input domain: ``ProcessDomain.VOLTAGE``.
        * output domain: ``ProcessDomain.VOLTAGE``.

    Args:
        load_capacitance (float): [unit: F] load capacitance.
        input_capacitance (float): [unit: F] input capacitance.
        t_sample (float): [unit: s] sampling time, which mainly consists of the amplifier's 
            settling time.
        t_hold (float): [unit: s] holding time, during which the amplifier is turned on and
            consumes power relentlessly.
        supply (float): [unit: V] supply voltage.
        gain_cl (int): amplifier's closed-loop gain. This gain describes the ratio of 
            ``input_capacitance`` over feedback capacitance.
        differential (bool): if using differential-input amplifier or single-input amplifier.
        noise (float): the stadard deviation of read noise, the default value is ``None``. If
            users do not specific this parameter, CamJ will calculate the noise STD based on 
            the kTC noise.
        ennable_prnu (bool): flag to enable PRNU. Default value is ``False``.
        prnu_std (float): the relative PRNU standard deviation respect to gain.
            PRNU gain standard deviation = prnu_std * gain. The default value is ``0.001``.
        enable_offset (bool): flag to enable adding offset voltage. Default value is ``False``.
        pixel_offset_voltage: pixel offset voltage in unit of volt (V). Default value is ``0.1``.
        col_offset_voltage: column-wise offset voltage in unit of volt (V). Default value is ``0.05``.
    """
    def __init__(
        self,
        # performance parameters
        load_capacitance = 1e-12,  # [F]
        input_capacitance = 1e-12,  # [F]
        t_sample = 2e-6,  # [s]
        t_hold = 10e-3,  # [s]
        supply = 1.8,  # [V]
        gain_cl = 2,
        differential = False,
        # noise parameters
        noise = None,
        enable_prnu = False,
        prnu_std = 0.001,
        enable_offset = False,
        pixel_offset_voltage = 0.1,
        col_offset_voltage = 0.05
    ):
        self.name = "ActiveBinning"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.VOLTAGE]
        self.output_domain = ProcessDomain.VOLTAGE

        # set input/output driver
        self.input_need_driver = True
        self.output_driver = False

        self.energy_model = ColumnAmplifierEnergy(
            load_capacitance = load_capacitance,
            input_capacitance = input_capacitance,
            t_sample = t_sample,
            t_hold = t_hold,
            supply = supply,
            gain_cl = gain_cl,
            differential = differential
        )

        if noise is None:
            noise = _single_pole_rc_circuit_thermal_noise(
                num_transistor = 8,
                inversion_level = "strong",
                capacitance = load_capacitance
            )
        gain = 1.0

        self.func_model = ColumnwiseFunc(
            name = "ColumnAmplifier",
            gain = gain,
            noise = noise,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std
        )

    def _set_binning_config(self, kernel_size):
        if len(kernel_size) != 1:
            raise Exception("The length of kernel_size, num_kernels and stride should be 1.")

        if kernel_size[0][-1] != 1:
            raise Exception("'PassiveBinning' only support kernel channel size of 1.")

        self.kernel_size = kernel_size[0][:2]

    def energy(self):
        """Calculate Energy

        To see the details of energy modeling, please check out:
            * ``analog.energy_model.ColumnAmplifierEnergy``.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        return self.energy_model.energy() * self.kernel_size[0] * self.kernel_size[1]

    def noise(self, input_signal_list):
        """Perform functional simulation

        This function simulates the functional behavior of binning.

        To see the details of function modeling, please refer:
            * ``analog.function_model.ColumnwiseFunc``.

        Args:
            input_signal_list (list): A list of input signals. Each input signal should be a 3D array.

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is a list of simulation results.
        """
        output_signal_list = []
        for input_signal in input_signal_list:
            input_shape = input_signal.shape
            if len(input_shape) != 3:
                raise Exception("'ActiveBinning' only support 3D input.")
            new_input_shape = (
                input_shape[0] // self.kernel_size[0],
                self.kernel_size[0],
                input_shape[1] // self.kernel_size[1],
                self.kernel_size[1],
                input_shape[2]
            )
            transposed_input_signal = np.transpose(
                input_signal.reshape(new_input_shape), 
                (0, 2, 1, 3, 4)
            ).reshape(
                (
                    new_input_shape[0],
                    new_input_shape[2],
                    new_input_shape[1] * new_input_shape[3],
                    new_input_shape[4]
                )
            )

            signal_after_colamp_list = []
            for i in range(new_input_shape[1] * new_input_shape[3]):
                signal_after_colamp_list.append(
                    self.func_model.simulate_output(
                        transposed_input_signal[:, :, i, :]
                    )
                )

            signal_sum = np.zeros(signal_after_colamp_list[0].shape)
            for signal_after_colamp in signal_after_colamp_list:
                signal_sum += signal_after_colamp

            output_signal_list.append(signal_sum / len(signal_after_colamp_list))

        return ("ActiveBinning", output_signal_list)


class Voltage2VoltageConv(object):
    """Voltage-to-Voltage Convolution

    This class performs convolution operations in analog domain. The convolution is realized by
    passive switched capacitor array, the capacitance of each capacitor is served as kernel weight.
    Source follower is used for signal readout.

    .. Note::
        Map corresponding ``WeightInput`` in software pipeline definition directly to this class 
        for correct functional simulation.

    Input/Output domains:
        * input domain: ``ProcessDomain.VOLTAGE``.
        * output domain: ``ProcessDomain.VOLTAGE``.

    Args:
        capacitance_array (array, float): [unit: F] a list of capacitors in passive switched capacitor array.
        vs_array (array, float): [unit: V] a list of voltages that corresponds to the voltage swing at each capacitor.
        sf_load_capacitance (float): [unit: F] load capacitance.
        sf_supply (float): [unit: V] supply voltage.
        sf_output_vs (float): [unit: V] voltage swing at the SF's output node.
        sf_bias_current (float): [unit: A] bias current.
        psca_noise (float): the stadard deviation of passive switched capacitor array's read noise,
            the default value is ``None``. If users do not specific this parameter, CamJ will 
            calculate the noise STD based on the kTC noise.
        sf_noise (float): the stadard deviation of SF read noise, the default value is ``None``. If
            users do not specific this parameter, CamJ will calculate the noise STD based on 
            the kTC noise.
        sf_enable_prnu (bool): flag to enable SF PRNU. Default value is ``False``.
        sf_prnu_std (float): the relative prnu standard deviation respect to SF gain.
                  prnu gain standard deviation = prnu_std * gain. the default value is ``0.001``.

    """
    def __init__(
        self,
        # peformance parameters
        capacitance_array,
        vs_array,
        sf_load_capacitance = 1e-12,  # [F]
        sf_supply = 1.8,  # [V]
        sf_output_vs = 1,  # [V]
        sf_bias_current = 5e-6,  # [A]
        # noise parameters
        psca_noise = None,
        sf_noise = None,
        sf_enable_prnu = False,
        sf_prnu_std = 0.001,
        
    ):
        self.name = "Voltage2VoltageConv"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.VOLTAGE]
        self.output_domain = ProcessDomain.VOLTAGE

        # set input/output driver
        self.input_need_driver = True
        self.output_driver = True

        if len(capacitance_array) != len(vs_array):
            raise Exception(
                "The length of 'capacitance_array' (%d) and the length of 'vs_array' (%d) should be the same!"\
                % (len(capacitance_array), len(vs_array))
            )

        self.kernel_size = None
        self.num_kernels = None
        self.stride = None
        self.len_capacitance_array = len(capacitance_array)
        self.psca_energy_model = PassiveSwitchedCapacitorArrayEnergy(
            capacitance_array = capacitance_array,
            vs_array = vs_array
        )

        self.sf_energy_model = SourceFollowerEnergy(
            load_capacitance = sf_load_capacitance,
            supply = sf_supply,
            output_vs = sf_output_vs,
            bias_current = sf_bias_current,
        )

        # here, we approximate the noise from PSCA.
        if psca_noise is None:
            psca_noise = _cap_thermal_noise(
                capacitance = np.mean(capacitance_array)
            )

        if sf_noise is None:
            sf_noise = _single_pole_rc_circuit_thermal_noise(
                num_transistor = 2,
                inversion_level = "strong",
                capacitance = sf_load_capacitance
            )
        sf_gain = 1.0

        # initialize random number generator
        self.psca_noise = psca_noise
        random_seed = int(time.time())
        self.rs = np.random.RandomState(random_seed)

        self.sf_func_model = PixelwiseFunc(
            name = "SourceFollower",
            gain = sf_gain,
            noise = sf_noise,
            enable_prnu = sf_enable_prnu,
            prnu_std = sf_prnu_std
        )

    def energy(self):
        """Calculate Energy

        To see the details of energy modeling, please check out:
            * ``analog.energy_model.PassiveSwitchedCapacitorArrayEnergy``.
            * ``analog.energy_model.SourceFollowerEnergy``.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        return self.psca_energy_model.energy() + self.sf_energy_model.energy()

    def _set_conv_config(self, kernel_size, num_kernels, stride):
        if len(kernel_size) != 1 or len(num_kernels) != 1 or len(stride) != 1:
            raise Exception("The length of kernel_size, num_kernels and stride should be 1.")

        if kernel_size[0][-1] != 1:
            raise Exception("'Voltage2VoltageConv' only support kernel channel size of 1.")

        self.kernel_size = kernel_size[0][:2]
        self.num_kernels = num_kernels[0]
        self.stride = stride[0][:2]

        if self.len_capacitance_array != self.kernel_size[0] * self.kernel_size[1]:
            raise Exception(
                "The length of capacitance_array (%d) doesn't match with kernel_size (%dx%d). "\
                 % (self.len_capacitance_array, self.kernel_size[0], self.kernel_size[1]))


    def _single_channel_convolution(self, input_signal, weight_signal):
        in_height, in_width = input_signal.shape    # Input shape
        w_height, w_width = weight_signal.shape     # weight shape
        s_height, s_width = self.stride             # stride shape
        out_height = (in_height - (w_height - s_height)) // s_height
        out_width = (in_width - (w_width - s_width)) // s_width
        # initialize output
        output_signal = np.zeros((out_height, out_width))

        for r in range(out_height):
            for c in range(out_width):
                # find the corresponding input elements for output
                input_elements = input_signal[
                    r*s_height : r*s_height+w_height,
                    c*s_width : c*s_width+w_width
                ]
                output_signal[r, c] = np.sum(input_elements * weight_signal)

        return output_signal

    def noise(self, input_signal_list):
        """Perform functional simulation

        This function simulates the functional behavior of convolution operation.

        To see the details of function modeling, please refer:
            * ``analog.function_model.PassiveSwitchedCapacitorArrayFunc``.
            * ``analog.function_model.PixelwiseFunc``.

        Args:
            input_signal_list (list): A list of input signals. One input should be input signal and the other one should be weight signal. 

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is a list of simulation results.
        """

        if len(input_signal_list) != 2:
            raise Exception("Input to Voltage2VoltageConv limits to 2 (input+weight)!")

        image_input = None
        kernel_input = None
        for input_signal in input_signal_list:
            if input_signal.shape[:2] == self.kernel_size[:2]:
                kernel_input = input_signal
            else:
                image_input = input_signal

        if image_input is None:
            raise Exception("Input signal to 'Voltage2VoltageConv' has not been initialized.")
        if kernel_input is None or kernel_input.shape[-1] != self.num_kernels:
            raise Exception(
                "Number of Kernel in input signal doesn't match the num_kernels (%d)"\
                % self.num_kernels
            )

        if image_input.ndim == 3:
            if image_input.shape[-1] != 1:
                raise Exception("image_input in 'Voltage2VoltageConv' need to be either (height, width) or (height, width, 1).")
            # squeeze image input to be 2D matrix
            image_input = np.squeeze(image_input)

        conv_result_list = []
        for i in range(self.num_kernels):
            conv_result = self._single_channel_convolution(image_input, kernel_input[:, :, i])
            output_height, output_width = conv_result.shape

            # apply noise to convolution result.
            conv_result_after_noise = self.rs.normal(
                scale = self.psca_noise,
                size = (output_height, output_width)
            ) + conv_result

            # apply sf noise
            conv_result_list.append(
                self.sf_func_model.simulate_output(
                    conv_result_after_noise
                )
            )

        output_height, output_width = conv_result_list[0].shape
        output_result = np.zeros((output_height, output_width, self.num_kernels))

        for i in range(self.num_kernels):
            output_result[:, :, i] = conv_result_list[i]

        return ("Voltage2VoltageConv", [output_result])



class Time2VoltageConv(object):
    """Time-to-Voltage Convolution

    This class performs convolution operations in analog domain. The convolution is realized by
    current mirror, the input current is used as kernel weight and the time signal from PWM pixel
    is used as input in convolution layer. Passive Analog Memory is used to store convolution output.
    [TODO:fixed] The memory accumulates convolutional partial sums sequentially.

    .. Note::
        Map corresponding ``WeightInput`` in software pipeline definition to a ``DigitalToCurrentConverter``
        and then connect the ``DigitalToCurrentConverter`` to this class for correct functional simulation.

    Input/Output domains:
        * input domain: ``ProcessDomain.CURRENT`` and ``ProcessDomain.TIME``.
        * output domain: ``ProcessDomain.VOLTAGE``.
    
    Args:
        cm_supply (float): [unit: V] supply voltage of current mirror.
        cm_load_capacitance (float): [unit: F] load capacitance of current mirror.
        cm_t_readout (float): [unit: s] readout time of current mirror, during which the constant current drives
            the load capacitance from 0 to VDD.
        cm_i_dc (float): [unit: A] the constant current of current mirror. If ``i_dc == None``, then i_dc is
            estimated from the other parameters.
        am_sample_capacitance (float): [unit: F] sample capacitance of passive analog memory.
        am_supply (float): [unit: V] supply voltage of passive analog memory.
        cm_noise (float): the standard deviation of current mirror read noise. Default value is ``None``. 
            If users do not specific this parameter, CamJ will calculate the noise STD based on 
            the kTC noise.
        cm_ennable_prnu (bool): flag to enable PRNU of current mirror. Default value is ``False``.
        cm_prnu_std (float): the relative PRNU standard deviation respect to current mirror gain.
            PRNU gain standard deviation = prnu_std * gain. The default value is ``0.001``.
        am_noise (float): the standard deviation of analog memory read noise. Default value is ``None``.
            If users do not specific this parameter, CamJ will calculate the noise STD based on 
            the kTC noise.
        am_ennable_prnu (bool): flag to enable PRNU of analog memory. Default value is ``False``.
        am_prnu_std (float): the relative PRNU standard deviation respect to gain of analog memory.
            PRNU gain standard deviation = prnu_std * gain. The default value is ``0.001``.
    """
    def __init__(
        self,
        # performance parameters for current mirror
        cm_supply = 1.8,
        cm_load_capacitance = 2e-12,  # [F]
        cm_t_readout = 1e-6,  # [s]
        cm_i_dc = 1e-6,  # [A]
        # performance parameters for analog memory
        am_sample_capacitance = 1e-12,  # [F]
        am_supply = 1.8,  # [V]
        # eqv_reso  # equivalent resolution
        # noise parameters for current mirror
        cm_noise = None,
        cm_enable_prnu = False,
        cm_prnu_std = 0.001,
        # noise parameters for analog memory
        am_noise = None,
        am_enable_prnu = False,
        am_prnu_std = 0.001,
        
    ):
        self.name = "Time2VoltageConv"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.TIME, ProcessDomain.CURRENT]
        self.output_domain = ProcessDomain.VOLTAGE

        # set input/output driver
        self.input_need_driver = False
        self.output_driver = False

        self.kernel_size = None
        self.num_kernels = None
        self.stride = None

        self.cm_energy_model = CurrentMirrorEnergy(
            supply = cm_supply,
            load_capacitance = cm_load_capacitance,
            t_readout = cm_t_readout,
            i_dc = cm_i_dc
        )

        self.am_energy_model = PassiveAnalogMemoryEnergy(
            sample_capacitance = am_sample_capacitance,
            supply = am_supply
        )

        if cm_noise is None:
            cm_noise = _single_pole_rc_circuit_thermal_noise(
                num_transistor = 1,
                inversion_level = "strong",
                capacitance = cm_load_capacitance
            )
        cm_gain = 1.0

        if am_noise is None:
            am_noise = _cap_thermal_noise(am_sample_capacitance)
        am_gain = 1.0

        self.cm_func_model = CurrentMirrorFunc(
            name = "CurrentMirror",
            gain = cm_gain,
            noise = cm_noise,
            enable_compute = True,
            enable_prnu = cm_enable_prnu,
            prnu_std = cm_prnu_std
        )

        self.am_func_model = PixelwiseFunc(
            name = "PassiveAnalogMemory",
            gain = am_gain,
            noise = am_noise,
            enable_prnu = am_enable_prnu,
            prnu_std = am_prnu_std
        )

    def energy(self):
        """Calculate Energy

        To see the details of energy modeling, please check out:
            * ``analog.energy_model.CurrentMirrorEnergy``.
            * ``analog.energy_model.PassiveAnalogMemoryEnergy``.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        if self.kernel_size is None:
            raise Exception("'kernel_size' in 'Time2CurrentConv' hasn't been initialized.")

        mac_cnt = self.kernel_size[0] * self.kernel_size[1]
        return self.cm_energy_model.energy() * mac_cnt + self.am_energy_model.energy() * 2

    def _set_conv_config(self, kernel_size, num_kernels, stride):
        if len(kernel_size) != 1 or len(num_kernels) != 1 or len(stride) != 1:
            raise Exception("In 'Time2VoltageConv', the length of kernel_size, num_kernels and stride should be 1.")

        if kernel_size[0][-1] != 1:
            raise Exception("'Time2VoltageConv' only support kernel channel size of 1.")

        self.kernel_size = kernel_size[0][:2]
        self.num_kernels = num_kernels[0]
        self.stride = stride[0][:2]


    def _single_channel_convolution(self, input_signal, weight_signal):
        in_height, in_width = input_signal.shape    # Input shape
        w_height, w_width = weight_signal.shape     # weight shape
        s_height, s_width = self.stride             # stride shape
        out_height = (in_height - (w_height - s_height)) // s_height
        out_width = (in_width - (w_width - s_width)) // s_width
        # initialize output
        output_signal = np.zeros((out_height, out_width))

        for r in range(out_height):
            for c in range(out_width):
                # find the corresponding input elements for output
                input_elements = input_signal[
                    r*s_height : r*s_height+w_height, 
                    c*s_width : c*s_width+w_width
                ]
                noise_output = self.cm_func_model.simulate_output(
                    input_signal = input_elements, 
                    weight_signal = weight_signal
                )
                output_signal[r, c] = np.sum(noise_output)

        return output_signal

    def noise(self, input_signal_list):
        """Perform functional simulation

        This function simulates the functional behavior of convolution operation.

        To see the details of function modeling, please refer:
            * ``analog.function_model.CurrentMirrorFunc``.
            * ``analog.function_model.PixelwiseFunc``.

        Args:
            input_signal_list (list): A list of input signals. One input should be input signal 
                and the other one should be weight signal. 

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is a list of simulation results.
        """
        if len(input_signal_list) != 2:
            raise Exception("Input to 'Time2VoltageConv' limits to 2 (input+weight)!")

        image_input = None
        kernel_input = None
        for input_signal in input_signal_list:
            if input_signal.shape[:2] == self.kernel_size[:2]:
                kernel_input = input_signal
            else:
                image_input = input_signal

        if image_input is None:
            raise Exception("Input signal to 'Time2VoltageConv' has not been initialized.")

        if kernel_input is None or kernel_input.shape[-1] != self.num_kernels:
            raise Exception(
                "Number of Kernel in input signal doesn't match the num_kernels (%d)"\
                % self.num_kernels
            )

        if image_input.ndim == 3:
            if image_input.shape[-1] != 1:
                raise Exception("image_input in 'Time2VoltageConv' need to be either (height, width) or (height, width, 1).")
            # squeeze image input to be 2D matrix
            image_input = np.squeeze(image_input)

        conv_result_list = []
        for i in range(self.num_kernels):
            conv_result = self._single_channel_convolution(image_input, kernel_input[:, :, i])
            output_height, output_width = conv_result.shape
            conv_result_list.append(
                self.am_func_model.simulate_output(
                    conv_result
                )
            )

        output_height, output_width = conv_result_list[0].shape
        output_result = np.zeros((output_height, output_width, self.num_kernels))

        for i in range(self.num_kernels):
            output_result[:, :, i] = conv_result_list[i]

        return ("Time2VoltageConv", [output_result])


class BinaryWeightConv(object):
    """Binary Weight Convolution [TODO: questionable]

    This class performs binary convolution operations in analog domain. All the kernel weights in this
    convolution operation should be either ``-1`` or ``1``. The convolution is realized by
    driving all positive weight input signals to one capacitor and all negative ones to another capacitor,
    and then, uses a comparator to generate the final output.

    .. Note::
        Map corresponding ``WeightInput`` in software pipeline definition directly to this class 
        for correct functional simulation.

    Input/Output domains:
        * input domain: ``ProcessDomain.VOLTAGE``.
        * output domain: ``ProcessDomain.VOLTAGE``.

    Args:
        load_capacitance (float): [unit: F] load capacitance.
        input_capacitance (float): [unit: F] input capacitance.
        t_sample (float): [unit: s] sampling time, which mainly consists of the amplifier's 
            settling time.
        t_hold (float): [unit: s] holding time, during which the amplifier is turned on and
            consumes power relentlessly.
        supply (float): [unit: V] supply voltage.
        gain_cl (int): amplifier's closed-loop gain. This gain describes the ratio of 
            ``input_capacitance`` over feedback capacitance.
        differential (bool): if using differential-input amplifier or single-input amplifier.
        noise (float): the standard deviation of read noise. Default value is ``None``.
        ennable_prnu (bool): flag to enable PRNU. Default value is ``False``.
        prnu_std (float): the relative PRNU standard deviation respect to gain.
            PRNU gain standard deviation = prnu_std * gain. The default value is ``0.001``.
        enable_offset (bool): flag to enable adding offset voltage. Default value is ``False``.
        pixel_offset_voltage: pixel offset voltage in unit of volt (V). Default value is ``0.1``.
        col_offset_voltage: column-wise offset voltage in unit of volt (V). Default value is ``0.05``.
    """
    def __init__(
        self,
        # performance parameters
        load_capacitance = 1e-12,  # [F]
        input_capacitance = 1e-12,  # [F]
        t_sample = 2e-6,  # [s]
        t_hold = 10e-3,  # [s]
        supply = 1.8,  # [V]
        gain_cl = 2,
        differential = False,
        # noise parameters
        noise = None,
        enable_prnu = False,
        prnu_std = 0.001,
        enable_offset = False,
        pixel_offset_voltage = 0.1,
        col_offset_voltage = 0.05
    ):
        self.name = "BinaryWeightConv"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.VOLTAGE]
        self.output_domain = ProcessDomain.VOLTAGE

        # set input/output driver
        self.input_need_driver = True
        self.output_driver = False

        self.kernel_size = None
        self.num_kernels = None
        self.stride = None

        self.energy_model = ColumnAmplifierEnergy(
            load_capacitance = load_capacitance,
            input_capacitance = input_capacitance,
            t_sample = t_sample,
            t_hold = t_hold,
            supply = supply,
            gain_cl = gain_cl,
            differential = differential
        )

        if noise is None:
            noise = _single_pole_rc_circuit_thermal_noise(
                num_transistor = 8,
                inversion_level = "strong",
                capacitance = load_capacitance
            )
        gain = 1.0

        self.func_model = ColumnwiseFunc(
            name = "ColumnAmplifier",
            gain = gain,
            noise = noise,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std
        )

    def energy(self):
        """Calculate Energy
        
        To see the details of energy modeling, please check out:
            * ``analog.energy_model.ColumnAmplifierEnergy``.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        return self.energy_model.energy()

    def _set_conv_config(self, kernel_size, num_kernels, stride):
        if len(kernel_size) != 1 or len(num_kernels) != 1 or len(stride) != 1:
            raise Exception("The length of kernel_size, num_kernels and stride should be 1.")

        if kernel_size[0][-1] != 1:
            raise Exception("'BinaryWeightConv' only support kernel channel size of 1.")

        if num_kernels[0] != 1:
            raise Exception("'BinaryWeightConv' only support num_kernels to be 1.")

        self.kernel_size = kernel_size[0][:2]
        self.num_kernels = num_kernels[0]
        self.stride = stride[0][:2]

    def _single_channel_convolution(self, input_signal, weight_signal):
        in_height, in_width = input_signal.shape    # Input shape
        w_height, w_width = weight_signal.shape     # weight shape
        s_height, s_width = self.stride             # stride shape
        out_height = (in_height - (w_height - s_height)) // s_height
        out_width = (in_width - (w_width - s_width)) // s_width
        # initialize output
        positive_output_signal = np.zeros((out_height, out_width))
        negative_output_signal = np.zeros((out_height, out_width))

        for r in range(out_height):
            for c in range(out_width):
                # find the corresponding input elements for output
                input_elements = input_signal[
                    r*s_height : r*s_height+w_height,
                    c*s_width : c*s_width+w_width
                ]
                positive_output_signal[r, c] = np.sum(input_elements[input_elements>=0])
                negative_output_signal[r, c] = np.sum(input_elements[input_elements< 0])

        return positive_output_signal, negative_output_signal

    def noise(self, input_signal_list):
        """Perform functional simulation

        This function simulates the functional behavior of convolution operation. This function
        inherits some functionalities from ``analog.function_model.ColumnwiseFunc``.

        To see the details of function modeling, please refer:
            * ``analog.function_model.ColumnwiseFunc``.

        Args:
            input_signal_list (list): A list of input signals. One input should be input signal 
                and the other one should be weight signal. 

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is a list of simulation results.
        """
        if len(input_signal_list) != 2:
            raise Exception("Input to 'BinaryWeightConv' limits to 2 (input+weight)!")

        image_input = None
        kernel_input = None
        for input_signal in input_signal_list:
            if input_signal.shape[:2] == self.kernel_size[:2]:
                kernel_input = input_signal
            else:
                image_input = input_signal

        if image_input is None:
            raise Exception("Input signal to 'BinaryWeightConv' has not been initialized.")
        if kernel_input is None or kernel_input.shape[-1] != self.num_kernels:
            raise Exception(
                "Number of Kernel in input signal doesn't match the num_kernels (%d)"\
                % self.num_kernels
            )

        if image_input.ndim == 3:
            if image_input.shape[-1] != 1:
                raise Exception("image_input in 'Time2VoltageConv' need to be either (height, width) or (height, width, 1).")
            # squeeze image input to be 2D matrix
            image_input = np.squeeze(image_input)
        
        positive_conv_signal, negative_conv_signal = self._single_channel_convolution(image_input, kernel_input[:, :, 0])
        output_height, output_width = positive_conv_signal.shape
        positive_conv_result = np.expand_dims(positive_conv_signal, axis = 2)
        negative_conv_result = np.expand_dims(negative_conv_signal, axis = 2)

        positive_result_after_noise = self.func_model.simulate_output(positive_conv_result)
        negative_result_after_noise = self.func_model.simulate_output(negative_conv_result)

        return ("BinaryWeightConv", [positive_result_after_noise, negative_result_after_noise])


class AnalogReLU(object):
    """Analog ReLU

    This class performs ReLU operation using analog comparator.
    Funtionally, this class performs ReLU after getting the convolutional results:
    the class outputs 0 when the result is negative and outputs the result as-is when the result is positive.
    Note that in real circuits the analog ReLU is performed before getting the convolutional results:
    the convolutional results are stored at two memories (positive part and negative part) based on the output polarity.
    If the positive part is smaller than the negative part, the output is set to 0; otherwise, the ReLU transfers the
    two parts as-is to the next analog processing stage. No subtractor is needed since the next stage usually takes
    differential inputs.

    Input/Output domains:
        * input domain: ``ProcessDomain.VOLTAGE``.
        * output domain: ``ProcessDomain.VOLTAGE``.
    
    Args:
        supply (float): [unit: V] supply voltage.
        i_bias (float): [unit: A] bias current of the circuit.
        t_readout (float): [unit: s] readout time, during which the comparison is finished.
        enable_prnu (bool): flag to enable PRNU. Default value is ``False``.
        prnu_std (float): the relative prnu standard deviation respect to gain.
                  prnu gain standard deviation = prnu_std * gain, the default value is ``0.001``.
    """
    def __init__(
        self,
        # performance parameters
        supply = 1.8,  # [V]
        i_bias = 10e-6,  # [A]
        t_readout = 1e-9,  # [s]
        # noise parameters
        enable_prnu = False,
        prnu_std = 0.001
    ):
        self.name = "AnalogReLU"
        # set input/output signal domain.
        self.input_domain = [ProcessDomain.VOLTAGE]
        self.output_domain = ProcessDomain.VOLTAGE

        # set input/output driver
        self.input_need_driver = False
        self.output_driver = False

        self.name = "ReLU"
        self.energy_model = ComparatorEnergy(
            supply = supply,
            i_bias = i_bias,
            t_readout = t_readout
        )

        self.func_model = ComparatorFunc(
            name = "Comparator",
            gain = 1,
            noise = 0,
            enable_prnu = enable_prnu,
            prnu_std = prnu_std
        )

    def energy(self):
        """Calculate Energy

        To see the details of energy modeling, please check out:
            * ``analog.energy_model.ComparatorEnergy``.

        Returns:
            float: the energy consumption of this analog compoenent in unit of ``J``.
        """
        return self.energy_model.energy()

    def noise(self, input_signal_list):
        """Perform functional simulation

        This function simulates the functional behavior of ReLU operation.

        To see the details of function modeling, please refer:
            * ``analog.function_model.ComparatorFunc``.

        Args:
            input_signal_list (list): A list of input signals. Each input signal should be a 3D array.

        Returns:
            Simulation result (tuple): The first element in the tuple is the name of this simulated
            analog component, the second one is a list of simulation results.
        """

        output_signal_list = []

        for input_signal in input_signal_list:
            zero_input_signal = np.zeros(input_signal.shape)
            output_signal_list.append(
                self.func_model.simulate_output(
                    input_signal1 = input_signal, 
                    input_signal2 = zero_input_signal
                )
            )

        return (self.name, output_signal_list)

