import numpy as np

from camj.sim_core.analog_perf_libs import ActivePixelSensorPerf, DigitalPixelSensorPerf,\
                                      PulseWidthModulationPixelPerf
from camj.functional_core.launch import default_functional_simulation
from camj.functional_core.noise_model import PhotodiodeNoise, PixelwiseNoise, FloatingDiffusionNoise,\
                                        CorrelatedDoubleSamplingNoise, AnalogToDigitalConverterNoise

# Active pxiel sensor
class ActivePixelSensor(object):
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
        # performance parameters
        pd_capacitance = 100e-15, # [F]
        pd_supply = 1.8, # [V]
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
        fd_noise = 0.,
        fd_prnu_std = 0.001,
        sf_gain = 1.0,
        sf_noise = 0.,
        sf_prnu_std = 0.001
    ):

        self.enable_cds = enable_cds
        if enable_cds:
            self.num_readout = 2
        else:
            self.num_readout = 1

        self.perf_model = ActivePixelSensorPerf(
            pd_capacitance = pd_capacitance,
            pd_supply = pd_supply,
            output_vs = output_vs,
            num_transistor = num_transistor,
            fd_capacitance = fd_capacitance,
            load_capacitance = load_capacitance,
            tech_node = tech_node,
            pitch = pitch,
            array_vsize = array_vsize
        )

        self.noise_components = [
            PhotodiodeNoise(
                name = "PDNoise",
                dark_current_noise = dark_current_noise,
                enable_dcnu = enable_dcnu,
                dcnu_std = dcnu_std
            ),
            FloatingDiffusionNoise(
                name = "FDNoise",
                gain = fd_gain,
                noise = fd_noise,
                enable_cds = enable_cds,
                enable_prnu = enable_prnu,
                prnu_std = fd_prnu_std
            ),
            PixelwiseNoise(
                name = "SFNoise",
                gain = sf_gain,
                noise = sf_noise,
                enable_prnu = enable_prnu,
                prnu_std = sf_prnu_std,
            )
        ]

    def energy(self):
        return self.perf_model.energy()

    def noise(self, input_signal_list):
        if not isinstance(input_signal_list, list):
            raise Exception("Input signal to APS needs to be a list of numpy array!")

        return default_functional_simulation(self.noise_components, input_signal_list)

# digital pixel sensor
class DigitalPixelSensor(object):
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
        # performance parameters
        pd_capacitance = 100e-15, # [F]
        pd_supply = 1.8, # [V]
        output_vs = 1,  # output voltage swing [V]
        num_transistor = 3,
        enable_cds = False,
        fd_capacitance = 10e-15,  # [F]
        load_capacitance = 1e-12,  # [F]
        tech_node = 130,  # [um]
        pitch = 4,  # [um]
        array_vsize = 128,
        # ADC performance parameters
        adc_type='SS',
        adc_fom=100e-15,  # [J/conversion]
        adc_reso=8,
        # noise parameters
        dark_current_noise = 0.,
        enable_dcnu = False,
        enable_prnu = False,
        dcnu_std = 0.001,
        # FD parameters
        fd_gain = 1.0,
        fd_noise = 0.,
        fd_prnu_std = 0.001,
        # SF parameters
        sf_gain = 1.0,
        sf_noise = 0.,
        sf_prnu_std = 0.001,
        # CDS parameters
        cds_gain = 1.0,
        cds_noise = 0.,
        cds_prnu_std = 0.001,
        # ADC parameters
        adc_noise = 0.,
    ):
        self.enable_cds = enable_cds
        if enable_cds:
            self.num_readout = 2
        else:
            self.num_readout = 1

        self.perf_model = DigitalPixelSensorPerf(
            pd_capacitance = pd_capacitance,
            pd_supply = pd_supply,
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

        self.noise_components = [
            PhotodiodeNoise(
                name = "PDNoise",
                dark_current_noise = dark_current_noise,
                enable_dcnu = enable_dcnu,
                dcnu_std = dcnu_std
            ),
            FloatingDiffusionNoise(
                name = "FDNoise",
                gain = fd_gain,
                noise = fd_noise,
                enable_cds = enable_cds,
                enable_prnu = enable_prnu,
                prnu_std = fd_prnu_std
            ),
            PixelwiseNoise(
                name = "SFNoise",
                gain = sf_gain,
                noise = sf_noise,
                enable_prnu = enable_prnu,
                prnu_std = sf_prnu_std,
            ),
        ]
        if self.enable_cds:
            self.noise_components.append(
                CorrelatedDoubleSamplingNoise(
                    name = "CDSNoise",
                    gain = cds_gain,
                    noise = cds_noise,
                    enable_prnu = enable_prnu,
                    prnu_std = cds_prnu_std
                )
            )
        self.noise_components.append(
            AnalogToDigitalConverterNoise(
                name = "ADCNoise",
                adc_noise = adc_noise,
                max_val = pd_supply
            )
        )

    def energy(self):
        return self.perf_model.energy()

    def noise(self, input_signal_list):
        if not isinstance(input_signal_list, list):
            raise Exception("Input signal to DPS needs to be a list of numpy array!")

        return default_functional_simulation(self.noise_components, input_signal_list)

class PulseWidthModulationPixel(object):
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
        pd_capacitance = 100e-15, # [F]
        pd_supply = 1.8, # [V]
        ramp_capacitance = 1e-12,  # [F]
        gate_capacitance = 10e-15,  # [F]
        num_readout = 1
    ):
        self.perf_model = PulseWidthModulationPixelPerf(
            pd_capacitance = pd_capacitance,
            pd_supply = pd_supply,
            ramp_capacitance = ramp_capacitance,
            gate_capacitance = gate_capacitance,
            num_readout = num_readout
        )

    def energy(self):
        return self.perf_model.energy()

    def noise(self, input_signal_list):
        raise Exception("Noise simulation for PWM pixel is not implemented yet!")


