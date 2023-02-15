import numpy as np
import math
import cv2
import time

class PhotodiodeNoise(object):
    """
        Noise model for photediode.

        This model simulates the behavior of photodiode, including shot noise, dark current
        and dark current non-uniformity.

        Input parameters:
            dark_current_noise: unit (e).
            enable_dcnu: flag to enable dark current non-uniformity
            dcnu_std: dcnu standard deviation percentage. it is relative number respect
                      to dark_current_noise, the dcnu standard deviation is,
                      dcnu_std * dark_current_noise, the default value is 0.001.
    """
    def __init__(self, 
        name,
        dark_current_noise,
        enable_dcnu = False,
        dcnu_std = 0.001,
    ):
        super(PhotodiodeNoise, self).__init__()
        self.name = name
        self.dark_current_noise = dark_current_noise
        self.enable_dcnu = enable_dcnu
        self.dcnu_noise = None
        self.dcnu_std = dcnu_std

        # initialize random number generator
        random_seed = int(time.time())
        self.rs = np.random.RandomState(random_seed)

    def apply_gain_and_noise(self, input_signal):
        if len(input_signal.shape) != 2:
            raise Exception("input signal in noise model needs to be in (height, width) 2D shape.")

        input_height, input_width = input_signal.shape

        # simulate photon shot noise using Poisson random function  
        signal_after_shot_noise = self.rs.poisson(input_signal, (input_height, input_width))

        # check if DCNU needs to be applied.
        if self.enable_dcnu:
            # first generate dcnu variant for each pixel
            if self.dcnu_noise is None or self.dcnu_noise.shape != input_signal.shape:  
                self.dcnu_noise = self.rs.normal(
                    loc = self.dark_current_noise,
                    scale = self.dark_current_noise * self.dcnu_std,
                    size = (input_height, input_width)
                )

            # then apply poisson distribution on dcnu
            signal_after_dc_noise = self.rs.poisson(
                self.dcnu_noise, 
                size = (input_height, input_width)
            ) + signal_after_shot_noise
        else:
            # directly apply dc noise
            signal_after_dc_noise = self.rs.poisson(
                self.dark_current_noise, 
                size = (input_height, input_width)
            ) + signal_after_shot_noise
            
        return np.clip(signal_after_dc_noise, a_min = 0, a_max = None)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class AnalogToDigitalConverterNoise(object):
    """
        ADC quantization noise model

        This model only considerthe coarse scale ADC noise, we don't split noise into details
        and we don't consider non-linear noise errors which can be calibrated during manufacture.

        Input parameters:
            adc_noise: the overall noise on ADC.
            max_val: the maximum value in ADC input. We assume the input voltage range is
                     from [0, max_val]
    """
    def __init__(
        self, 
        name,
        adc_noise,
        max_val
    ):
        super(AnalogToDigitalConverterNoise, self).__init__()
        self.name = name
        self.adc_noise = adc_noise
        self.max_val = max_val

        # initialize random number generator
        random_seed = int(time.time())
        self.rs = np.random.RandomState(random_seed)

    def apply_gain_and_noise(self, input_signal):
        if len(input_signal.shape) != 2:
            raise Exception("input signal in noise model needs to be in (height, width) 2D shape.")

        input_height, input_width = input_signal.shape

        # simulate quantization noise
        signal_after_noise = self.rs.normal(
            scale = self.adc_noise,
            size = (input_height, input_width)
        ) + input_signal

        return np.clip(signal_after_noise, a_min = 0, a_max = self.max_val)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class AbsoluteDifferenceNoise(object):
    """
        A noise model for absolute difference

        This noise model simulates the noises happened in absolute difference operation.
        Two inputs will first compute the absolute difference, and then, apply gain and noises.
        The mathematical equation is
            res = gain * (abs(in1 - in2)) + noise

        Input parameters:
            gain: the gain applied in absolute difference, the default value is 1.
            noise: the read noise happened during readout absolute result. unit: V.
            enable_prnu: flag to enable PRNU.
            prnu_std: the relative prnu standard deviation respect to gain.
                      prnu gain standard deviation = prnu_std * gain.
                      the default value is 0.001

    """
    def __init__(
        self,
        name,
        gain = 1,
        noise = None,
        enable_prnu = False,
        prnu_std = 0.001
    ):
        super(AbsoluteDifferenceNoise, self).__init__()
        self.name = name
        self.gain = gain
        self.noise = noise
        self.enable_prnu = enable_prnu
        self.prnu_std = prnu_std
        self.prnu_gain = None

        if self.noise == None:
            raise Exception("Insufficient parameters: noise is None.")

        # initialize random number generator
        random_seed = int(time.time())
        self.rs = np.random.RandomState(random_seed)

    def apply_gain_and_noise(self, input_signal1, input_signal2):
        if len(input_signal1.shape) != 2 or len(input_signal2.shape) != 2:
            raise Exception("input signal in noise model needs to be in (height, width) 2D shape.")
                
        if input_signal1.shape != input_signal2.shape:
            raise Exception("Two input shapes are not equal in absolute difference!")

        diff_signal = np.abs(input_signal1 - input_signal2)

        input_height, input_width = diff_signal.shape
        if self.enable_prnu:
            if self.prnu_gain is None or self.prnu_gain.shape != diff_signal.shape:
                self.prnu_gain = self.rs.normal(
                    loc = self.gain,
                    scale = self.gain * self.prnu_std,
                    size = (input_height, input_width)
                )
            # generate random gain values
            diff_after_gain = self.prnu_gain * diff_signal
        else:
            diff_after_gain = self.gain * diff_signal

        diff_after_noise = self.rs.normal(
            scale = self.noise,
            size = (input_height, input_width)
        ) + diff_after_gain

        return np.clip(diff_after_noise, a_min = 0, a_max = None)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class CurrentMirrorNoise(object):
    """
        Noise model for current mirror

        Current mirror has two possible outputs:
        1. output charge: in this case, the input current will multiply with integrated time and 
        output the charge which is (current*time).
        2. output current: in this case, there is no computation, just perform gain amplification.

        Input parameters:
            gain: the average gain.
            noise: average noise value.
            enable_compute: flag to enable compute and output charges.
            enable_prnu: flag to enable PRNU.
            prnu_std: the relative prnu standard deviation respect to gain.
                      prnu gain standard deviation = prnu_std * gain.
                      the default value is 0.001
    """
    def __init__(
        self,
        name,
        gain = 1,
        noise = None,
        enable_compute = False,
        enable_prnu = False,
        prnu_std = 0.001
    ):
        super(PixelwiseNoise, self).__init__()
        self.name = name
        self.gain = gain
        self.noise = noise
        self.enable_compute = enable_compute
        self.enable_prnu = enable_prnu
        self.prnu_gain = None
        self.prnu_std = prnu_std

        if self.noise == None:
            raise Exception("Insufficient parameters: noise is None.")

        # initialize random number generator
        random_seed = int(time.time())
        self.rs = np.random.RandomState(random_seed)

    def apply_gain_and_noise(self, input_signal, weight_signal=None):
        if len(input_signal.shape) != 2:
            raise Exception("input signal in noise model needs to be in (height, width) 2D shape.")
                
        if self.enable_compute and weight_signal is not None:
            input_signal = input_signal * weight_signal

        input_height, input_width = input_signal.shape
        if self.enable_prnu:
            if self.prnu_gain is None or self.prnu_gain.shape != input_signal.shape:
                self.prnu_gain = self.rs.normal(
                    loc = self.gain,
                    scale = self.gain * self.prnu_std,
                    size = (input_height, input_width)
                )
            # generate random gain values
            input_after_gain = self.prnu_gain * input_signal
        else:
            input_after_gain = self.gain * input_signal

        input_after_noise = self.rs.normal(
            scale = self.noise,
            size = (input_height, input_width)
        ) + input_after_gain

        return np.clip(input_after_noise, a_min = 0, a_max = None)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class PassiveSwitchedCapacitorArrayNoise(object):
    """
        Noise model for passive switched capacitor array

        Input parameters:
            num_capacitor: number of capacitor in capacitor array
            noise: average noise value.
            enable_prnu: flag to enable PRNU.
            prnu_std: the relative prnu standard deviation respect to gain.
                      prnu gain standard deviation = prnu_std * gain.
                      the default value is 0.001
    """
    def __init__(
        self,
        name,
        num_capacitor,
        noise = None
    ):
        super(PixelwiseNoise, self).__init__()
        self.name = name
        self.num_capacitor = num_capacitor
        self.noise = noise

        if self.noise == None:
            raise Exception("Insufficient parameters: noise is None.")

        # initialize random number generator
        random_seed = int(time.time())
        self.rs = np.random.RandomState(random_seed)

    def apply_gain_and_noise(self, input_signal_list):
        if len(input_signal_list) != self.num_capacitor:
            raise Exception(
                "Input signal list length (%d) needs to be equal to the number of capacitor (%d)!"\
                % (len(input_signal_list, self.num_capacitor)))

        if len(input_signal_list[0].shape) != 2:
            raise Exception("input signal in noise model needs to be in (height, width) 2D shape.")
            
        input_shape = input_signal_list[0].shape

        for input_signal in input_signal_list:
            if input_signal.shape != input_shape:
                raise Exception("Input signal shapes in list are not consistent!")

        average_input_signal = np.zeros(input_shape)

        for input_signal in input_signal_list:
            average_input_signal += input_signal

        average_input_signal = average_input_signal / len(input_signal_list)

        input_height, input_width = average_input_signal.shape

        input_after_noise = self.rs.normal(
            scale = self.noise,
            size = (input_height, input_width)
        ) + average_input_signal

        return np.clip(input_after_noise, a_min = 0, a_max = None)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class PixelwiseNoise(object):
    """
        A general interface for any noise source resided inside each pixel,
        including floating diffusion, source follower, etc.

        General assumption of the noise source is that the noise follows 
        a "zero-mean" Gaussian distribution. Users need to provide mean noise (sigma value).

        The computation follows first applying gain to the input and then sampling noise.

        Input parameters:
            gain: the average gain.
            noise: average noise value.
            enable_prnu: flag to enable PRNU.
            prnu_std: the relative prnu standard deviation respect to gain.
                      prnu gain standard deviation = prnu_std * gain.
                      the default value is 0.001
    """
    def __init__(
        self,
        name,
        gain = 1,
        noise = None,
        enable_prnu = False,
        prnu_std = 0.001
    ):
        super(PixelwiseNoise, self).__init__()
        self.name = name
        self.gain = gain
        self.noise = noise
        self.enable_prnu = enable_prnu
        self.prnu_gain = None
        self.prnu_std = prnu_std

        if self.noise == None:
            raise Exception("Insufficient parameters: noise is None.")

        # initialize random number generator
        random_seed = int(time.time())
        self.rs = np.random.RandomState(random_seed)

    def apply_gain_and_noise(self, input_signal):
        if len(input_signal.shape) != 2:
            raise Exception("input signal in noise model needs to be in (height, width) 2D shape.")
                
        input_height, input_width = input_signal.shape
        if self.enable_prnu:
            if self.prnu_gain is None or self.prnu_gain.shape != input_signal.shape:
                self.prnu_gain = self.rs.normal(
                    loc = self.gain,
                    scale = self.gain * self.prnu_std,
                    size = (input_height, input_width)
                )
            # generate random gain values
            input_after_gain = self.prnu_gain * input_signal
        else:
            input_after_gain = self.gain * input_signal

        input_after_noise = self.rs.normal(
            scale = self.noise,
            size = (input_height, input_width)
        ) + input_after_gain

        return np.clip(input_after_noise, a_min = 0, a_max = None)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class FloatingDiffusionNoise(object):
    """
        Floating Diffusion class

        General assumption of the noise source is that the noise 
        follows a "zero-mean" Gaussian distribution. Users need 
        to provide the average noise error (sigma value).

        Gain is generally slightly less than 1, here, the default value
        is 1.

        To enable CDS and PRNU, just set enable flag to be True.

        if enable_cds is True, apply_gain_and_noise function will
        return two values, one is the input + reset noise, 
        and the other is the reset noise.

        Order: gain will be first applied before adding noises.

        Input parameters:
            gain: the average gain value.
            noise: the average noise value.
            enable_cds: flag to enable CDS (correlated double sampling).
            enable_prnu: flag to enable PRNU.
            prnu_std: the relative prnu standard deviation respect to gain.
                      prnu gain standard deviation = prnu_std * gain.
                      the default value is 0.001
    """
    def __init__(
        self,
        name,
        gain = 1,
        noise = None,
        enable_cds = False,
        enable_prnu = False,
        prnu_std = 0.001

    ):
        super(FloatingDiffusionNoise, self).__init__()
        self.name = name
        self.gain = gain
        self.noise = noise
        self.enable_cds = enable_cds
        self.enable_prnu = enable_prnu
        self.prnu_gain = None
        self.prnu_std = prnu_std

        if self.noise == None:
            raise Exception("Insufficient parameters: noise is None.")

        # initialize random number generator
        random_seed = int(time.time())
        self.rs = np.random.RandomState(random_seed)

    def apply_gain_and_noise(self, input_signal):
        if len(input_signal.shape) != 2:
            raise Exception("input signal in noise model needs to be in (height, width) 2D shape.")
                
        input_height, input_width = input_signal.shape
        if self.enable_prnu:
            if self.prnu_gain is None or self.prnu_gain.shape != input_signal.shape:
                self.prnu_gain = self.rs.normal(
                    loc = self.gain,
                    scale = self.gain*self.prnu_std,
                    size = (input_height, input_width)
                )
            # generate random gain values
            input_after_gain = self.prnu_gain * input_signal
        else:
            input_after_gain = self.gain * input_signal

        reset_noise = self.rs.normal(
            scale = self.noise,
            size = (input_height, input_width)
        )
        input_after_noise = reset_noise + input_after_gain

        if self.enable_cds:
            return np.clip(input_after_noise, a_min=0, a_max=None), \
                   np.clip(reset_noise, a_min=0, a_max=None)
        else:
            return np.clip(input_after_noise, a_min=0, a_max=None)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class CorrelatedDoubleSamplingNoise(object):
    """
        Correlated Double Sampling

        noise model for correlated double sampling module.

        General assumption of CDS is gain is 1, read noise follows zero-mean normal distribution.
        Mathematical expression for CDS:
            output = (input_signal - reset_signal) * gain + noise

        Input parameters:
            gain: the average gain value.
            noise: the average noise value.ß
            enable_prnu: flag to enable PRNU.
            prnu_std: the relative prnu standard deviation respect to gain.
                      prnu gain standard deviation = prnu_std * gain.
                      the default value is 0.001
        
    """
    def __init__(
        self,
        name,
        gain = 1,
        noise = None,
        enable_prnu = False,
        prnu_std = 0.001
    ):
        super(CorrelatedDoubleSamplingNoise, self).__init__()
        self.name = name
        self.gain = gain
        self.noise = noise
        self.enable_prnu = enable_prnu
        self.prnu_std = prnu_std
        self.prnu_gain = None

        if self.noise == None:
            raise Exception("Insufficient parameters: noise is None.")

        # initialize random number generator
        random_seed = int(time.time())
        self.rs = np.random.RandomState(random_seed)

    def apply_gain_and_noise(self, input_signal, reset_noise):
        if len(input_signal.shape) != 2:
            raise Exception("input signal in noise model needs to be in (height, width) 2D shape.")
                
        input_height, input_width = input_signal.shape

        input_diff = input_signal - reset_noise

        if self.enable_prnu:
            if self.prnu_gain is None or self.prnu_gain.shape != input_signal.shape:
                self.prnu_gain = self.rs.normal(
                    loc = self.gain,
                    scale = self.gain*self.prnu_std,
                    size = (input_height, input_width)
                )
            # generate random gain values
            input_after_gain = self.prnu_gain * input_diff
        else:
            input_after_gain = self.gain * input_diff


        input_after_noise = self.rs.normal(
            scale = self.noise,
            size = (input_height, input_width)
        ) + input_after_gain

        return np.clip(input_after_noise, a_min=0, a_max=None)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class ComparatorNoise(object):
    """
        Comparator noise model

        General assumption:
            gain is 1,
            noise follows zero-mean normal distribution.

        Order: gain will be first applied before adding noises.

        Input parameters:
            gain: the average gain value.
            noise: the average noise value.
            enable_prnu: flag to enable PRNU.
            prnu_std: the relative prnu standard deviation respect to gain.
                      prnu gain standard deviation = prnu_std * gain.
                      the default value is 0.001
    """
    def __init__(
        self,
        name,
        gain = 1,
        noise = None,
        enable_prnu = False,
        prnu_std = 0.001
    ):
        super(ComparatorNoise, self).__init__()
        self.name = name
        self.gain = gain
        self.noise = noise
        self.enable_prnu = enable_prnu
        self.prnu_std = prnu_std
        self.prnu_gain = None

        if self.noise == None:
            raise Exception("Insufficient parameters: noise is None.")

        # initialize random number generator
        random_seed = int(time.time())
        self.rs = np.random.RandomState(random_seed)

    def apply_gain_and_noise(self, input_signal1, input_signal2):
        if len(input_signal1.shape) != 2:
            raise Exception("input signal in noise model needs to be in (height, width) 2D shape.")
                
        input_height, input_width = input_signal1.shape

        input_diff = input_signal1 - input_signal2

        if self.enable_prnu:
            if self.prnu_gain is None or self.prnu_gain.shape != input_signal.shape:
                self.prnu_gain = self.rs.normal(
                    loc = self.gain,
                    scale = self.gain*self.prnu_std,
                    size = (input_height, input_width)
                )
            # generate random gain values
            input_after_gain = self.prnu_gain * input_diff
        else:
            input_after_gain = self.gain * input_diff

        input_after_noise = self.rs.normal(
            scale = self.noise,
            size = (input_height, input_width)
        ) + input_after_gain

        # find value greater than 0 and mask them 1.
        result = np.zeros((input_height, input_width))
        result[input_after_noise>=0] = 1

        return result

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class ColumnwiseNoise(object):
    """
        A general interface for any noise source that applies to
        each column, such as column amplifier.

        Assumption for this class is that it has a row-like struction such as column amplifier,
        and this class can capture the different properties in columnwise structure.
        One example is the column amplifier has PRNU columnwise.

        Mathematical equation:
            output = gain * in + noise

        Input parameters:
            gain: the average gain value.
            noise: the average noise value.
            max_val: the maximum value of the input range.
            enable_prnu: flag to enable PRNU.
            prnu_std: the relative prnu standard deviation respect to gain.
                      prnu gain standard deviation = prnu_std * gain.
                      the default value is 0.001
    """
    def __init__(
        self,
        name,
        gain=1,
        noise=None,
        enable_prnu=False,
        prnu_std=0.001,
        enable_offset=False,
        pixel_offset_voltage=0.1,
        col_offset_voltage=0.05
    ):
        super(ColumnwiseNoise, self).__init__()
        self.name = name
        self.gain = gain
        self.noise = noise
        self.enable_prnu = enable_prnu
        self.prnu_gain = None
        self.prnu_std = prnu_std
        self.enable_offset = enable_offset
        self.pixel_offset_voltage = pixel_offset_voltage
        self.col_offset_voltage = col_offset_voltage
        self.prnu_gain = None

        if self.noise == None:
            raise Exception("Insufficient parameters: noise is None.")

        # initialize random number generator
        random_seed = int(time.time())
        self.rs = np.random.RandomState(random_seed)

    def apply_gain_and_noise(self, input_signal):
        if len(input_signal.shape) != 2:
            raise Exception("input signal in noise model needs to be in (height, width) 2D shape.")
                
        input_height, input_width = input_signal.shape
        if self.enable_offset:
            input_signal += self.pixel_offset_voltage
        if self.enable_prnu:
            if self.prnu_gain is None or self.prnu_gain.shape != input_signal.shape:
                self.prnu_gain = np.repeat(
                    self.rs.normal(
                        loc = self.gain,
                        scale = self.gain*self.prnu_std,
                        size = (1, input_width)
                    ),
                    input_height,
                    axis=0
                )
            # generate random gain values
            input_after_gain = self.prnu_gain * input_signal
        else:
            input_after_gain = self.gain * input_signal

        input_after_noise = self.rs.normal(
            scale = self.noise,
            size = (input_height, input_width)
        ) + input_after_gain

        if self.enable_offset:
            input_after_gain += self.col_offset_voltage

        return np.clip(input_after_noise, a_min=0, a_max=None)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


