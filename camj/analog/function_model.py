"""Func Model Module

This module includes all basic noise model for CamJ functional simulation.

.. note::
    CamJ models the output of each component by applying a gain and a read noise to its input.
    Analytically, the model performs ``output = input * gain + read_noise``.
    This formula implies that we only consider two main types of hardware non-idealities: gain variation (or, PRNU) and read noise (zero-mean Gaussian).

.. note::
    Because nearly all of our implemented components are linear circuits which have linear transfer functions, we can use "gain" and "gain variation"
    as the proxy to describe the component's functional behavior.
    The proxy is also applicable to ADCs and comparators which are non-linear (but uniform) circuits because their transfer functions have linear frontiers.
    The proxy is also applicable to other non-linear circuits, such as the circuit that performs quantize(log(x1/x2)) in [JSSC-2019],
    by using a set of "gain" and "gain variation" to approximate the non-linear transfer function in piece-wise linear manner.
    Note that the proxy doesn't always reflect the physical reality of the circuit, meaning that the "gain" may not be an explicit
    parameter in the circuit and the "gain variation" is not analytically derived from the circuit parameters.
    However, the proxy trades low level circuit details off for the model's simplicity.
"""

import numpy as np
import math
import time
import copy


class PhotodiodeFunc(object):
    """Func model for photediode.

    This model simulates the behavior of photodiode, including shot noise, dark current
    and dark current non-uniformity.

    Mathematical Expression:
        output_signal = Poisson(x_in) + Norm(DCNU * dark_current)

    Args:
        name (str): the name of this noise.
        dark_current_noise (float): average dark current noise in unit of electrons (e-).
        enable_dcnu (bool): flag to enable dark current non-uniformity, the default value is ``False``.
        dcnu_std (float): dcnu standard deviation percentage. it is relative number respect
            to ``dark_current_noise``, the dcnu standard deviation is,
            ``dcnu_std`` * ``dark_current_noise``, the default value is 0.001.

    """
    def __init__(self, 
        name: str,
        dark_current_noise: float,
        enable_dcnu = False,
        dcnu_std = 0.001,
    ):
        super(PhotodiodeFunc, self).__init__()
        self.name = name
        self.dark_current_noise = dark_current_noise
        self.enable_dcnu = enable_dcnu
        self.dcnu_noise = None
        self.dcnu_std = dcnu_std

        # initialize random number generator
        random_seed = int(time.time())
        self.rs = np.random.RandomState(random_seed)

    def simulate_output(self, input_signal):
        """apply gain and noise to input signal

        Args:
            input_signal: input signal to photodiode in unit of photons in a 2D tensor.

        Returns:
            2D tensor: signal out of photodiode in unit of voltage.
        """

        input_shape = input_signal.shape

        # simulate photon shot noise using Poisson random function  
        signal_after_shot_noise = self.rs.poisson(input_signal, input_shape)

        # check if DCNU needs to be applied.
        if self.enable_dcnu:
            # first generate dcnu variant for each pixel
            if self.dcnu_noise is None or self.dcnu_noise.shape != input_signal.shape:  
                self.dcnu_noise = self.rs.normal(
                    loc = self.dark_current_noise,
                    scale = self.dark_current_noise * self.dcnu_std,
                    size = input_shape
                )

            # then apply poisson distribution on dcnu
            signal_after_dc_noise = self.rs.poisson(
                self.dcnu_noise, 
                size = input_shape
            ) + signal_after_shot_noise
        else:
            # directly apply dc noise
            signal_after_dc_noise = self.rs.poisson(
                self.dark_current_noise, 
                size = input_shape
            ) + signal_after_shot_noise
            
        return np.clip(signal_after_dc_noise, a_min = 0, a_max = None)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class AnalogToDigitalConverterFunc(object):
    """ADC quantization noise model

    This model only consider a coarse-scale ADC noise, which we model in normal distribution.
    We don't consider non-linear noise errors which can be calibrated during manufacture.

    Mathematical Expression:
        output_signal = Quantization(input_signal + Norm(adc_noise))

    Args:
        name (str): the name of the noise.
        adc_noise (float): the overall noise on ADC.
        max_val (float): the maximum value in ADC input. We assume the input voltage range is
            from [0, max_val]
        resolution (int): the resolution of the output value in digital domain. ``8`` means
            the maximum value in digital value is ``8^2 - 1`` == ``255`` bit.
    """ 
    def __init__(
        self, 
        name: str,
        adc_noise: float,
        max_val: float,
        resolution: int
    ):
        super(AnalogToDigitalConverterFunc, self).__init__()
        self.name = name
        self.adc_noise = adc_noise
        self.max_val = max_val
        self.max_resolution_val = 2 ** resolution - 1

        # initialize random number generator
        random_seed = int(time.time())
        self.rs = np.random.RandomState(random_seed)

    def simulate_output(self, input_signal):
        """apply gain and noise to input signal

        Args:
            input_signal: input signal to ADC in unit of voltage in a 2D/3D tensor.

        Returns:
            2D/3D tensor: digital values after quantization of ADC.
        """

        input_shape = input_signal.shape

        # simulate quantization noise
        signal_after_noise = self.rs.normal(
            scale = self.adc_noise,
            size = input_shape
        ) + input_signal

        return np.clip(signal_after_noise, a_min = 0, a_max = self.max_val) / self.max_val * self.max_resolution_val

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class AbsoluteDifferenceFunc(object):
    """A noise model for absolute difference

    This noise model simulates the noises happened in absolute difference operation.
    Two inputs will first compute the absolute difference, and then, apply gain and noises.
    
    Mathematical Expression:
        out = gain * (Abs(in1 - in2)) + Norm(noise)

    Args:
        name (str): the name of the noise.
        gain (float): the gain applied in absolute difference, the default value is ``1.0``.
        noise (float): the read noise standard deviation during readout in the unit of voltage (V).
        enable_prnu (bool): flag to enable PRNU. Default value is ``False``.
        prnu_std (float): relative PRNU standard deviation respect to gain. 
            PRNU gain standard deviation = prnu_std * gain. The default value is ``0.001``.

    """
    def __init__(
        self,
        name: str,
        gain = 1.0,
        noise = None,
        enable_prnu = False,
        prnu_std = 0.001
    ):
        super(AbsoluteDifferenceFunc, self).__init__()
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

    def simulate_output(self, input_signal1, input_signal2):
        """apply gain and noise to input signal

        Args:
            input_signal1: the first input signal to ABS component in a 2D/3D tensor.
            input_signal2: the second input signal to ABS component in a 2D/3D tensor.

        Returns:
            2D/3D tensor: signal values after ABS component.
        """       
        if input_signal1.shape != input_signal2.shape:
            raise Exception("Two input shapes are not equal in absolute difference!")

        diff_signal = np.abs(input_signal1 - input_signal2)

        input_shape = diff_signal.shape
        if self.enable_prnu:
            if self.prnu_gain is None or self.prnu_gain.shape != diff_signal.shape:
                self.prnu_gain = self.rs.normal(
                    loc = self.gain,
                    scale = self.gain * self.prnu_std,
                    size = input_shape
                )
            # generate random gain values
            diff_after_gain = self.prnu_gain * diff_signal
        else:
            diff_after_gain = self.gain * diff_signal

        diff_after_noise = self.rs.normal(
            scale = self.noise,
            size = input_shape
        ) + diff_after_gain

        return np.clip(diff_after_noise, a_min = 0, a_max = None)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class CurrentMirrorFunc(object):
    """A noise model for current mirror

    Current mirror has two possible outputs to model two functionalities of current mirror.
    1. output charge: in this case, the input current will multiply with integrated time and 
    output the charge which is ``current*time``.
    2. output current: in this case, there is no computation, just perform gain amplification.

    Mathematical Expression:
        1. out = gain * (input_signal * weight_signal) + Norm(noise)
        2. out = gain * input_signal + Norm(noise).

    Args:
        name (str): the name of the noise.
        gain (float): the average gain. Default value is ``1.0``.
        noise (float): the standard deviation of read noise. Default value is ``None``.
        enable_compute (bool): flag to enable compute and output charges. Default value is ``False``.
        enable_prnu (bool): flag to enable PRNU. Default value is ``False``.
        prnu_std (float): the relative prnu standard deviation respect to gain.
            prnu gain standard deviation = prnu_std * gain. The default value is ``0.001``.
    """
    def __init__(
        self,
        name: str,
        gain = 1,
        noise = None,
        enable_compute = False,
        enable_prnu = False,
        prnu_std = 0.001
    ):
        super(CurrentMirrorFunc, self).__init__()
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

    def simulate_output(self, input_signal, weight_signal=None):
        """apply gain and noise to input signal

        Args:
            input_signal: the input signal to current mirror in a 2D/3D tensor.
            weight_signal: the weight signal to current mirror in a 2D/3D tensor.

        Returns:
            2D/3D tensor: signal values after current mirror.
        """
        if weight_signal is not None:
            if input_signal.shape != weight_signal.shape:
                raise Exception("Two inputs, input_signal and weight_signal need to be in the same shape.")

        # initialize a new output matrix, avoid overwrite the input.
        output_signal = np.zeros(input_signal.shape)
        if self.enable_compute:
            if weight_signal is not None:
                output_signal = input_signal * weight_signal
            else:
                raise Exception("Weight signal is missing when compute is enabled in current mirror.")
        else:
            output_signal = copy.deepcopy(input_signal)

        input_shape = input_signal.shape
        # enable prnu and generate gain variance.
        if self.enable_prnu:
            if self.prnu_gain is None or self.prnu_gain.shape != input_signal.shape:
                # generate random gain values
                self.prnu_gain = self.rs.normal(
                    loc = self.gain,
                    scale = self.gain * self.prnu_std,
                    size = input_shape
                )
            input_after_gain = self.prnu_gain * output_signal
        else:
            input_after_gain = self.gain * output_signal

        input_after_noise = self.rs.normal(
            scale = self.noise,
            size = input_shape
        ) + input_after_gain

        return input_after_noise

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class PassiveSwitchedCapacitorArrayFunc(object):
    """A noise model for passive switched capacitor array

    Passive switched capacitor array can realize many mathematical operations such as
    average, addition, multiplication.

    Mathematical Expression:
        out = Average(in_1, ..., in_N)  + Norm(noise)

    Args:
        name (str): the name of the noise.
        num_capacitor (int): number of capacitor in capacitor array.
        noise (float): the standard deviation of read noise. Default value is ``None``.
    """
    def __init__(
        self,
        name,
        num_capacitor,
        noise = None
    ):
        super(PassiveSwitchedCapacitorArrayFunc, self).__init__()
        self.name = name
        self.num_capacitor = num_capacitor
        self.noise = noise

        if self.noise == None:
            raise Exception("Insufficient parameters: noise is None.")

        # initialize random number generator
        random_seed = int(time.time())
        self.rs = np.random.RandomState(random_seed)

    def simulate_output(self, input_signal_list: list):
        """apply gain and noise to input signal

        Args:
            input_signal_list: a list of input signals to passive switched capacitor array.

        Returns:
            2D/3D tensor: averaged signal value after passive switched capacitor array.
        """
        if len(input_signal_list) != self.num_capacitor:
            raise Exception(
                "Input signal list length (%d) needs to be equal to the number of capacitor (%d)!"\
                % (len(input_signal_list), self.num_capacitor))

        input_shape = input_signal_list[0].shape

        for input_signal in input_signal_list:
            if input_signal.shape != input_shape:
                raise Exception("Input signal shapes in list are not consistent!")

        average_input_signal = np.zeros(input_shape)

        for input_signal in input_signal_list:
            average_input_signal += input_signal

        average_input_signal = average_input_signal / len(input_signal_list)

        input_shape = average_input_signal.shape

        input_after_noise = self.rs.normal(
            scale = self.noise,
            size = input_shape
        ) + average_input_signal

        return input_after_noise

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class MaximumVoltageFunc(object):
    """A noise model for max voltage array.

    Maximum voltage produce element-wise maximum for a list of input signals. It is 
    used for operations like MaxPool.

    Mathematical Expression:
        out = Max(in_1, ..., in_N) + Norm(noise)

    Args:
        name (str): the name of the noise.
        noise (float): the standard deviation of read noise. Default value is ``None``.
    """
    def __init__(
        self,
        name,
        noise = None
    ):
        super(MaximumVoltageFunc, self).__init__()
        self.name = name
        self.noise = noise

        if self.noise == None:
            raise Exception("Insufficient parameters: noise is None.")

        # initialize random number generator
        random_seed = int(time.time())
        self.rs = np.random.RandomState(random_seed)

    def simulate_output(self, input_signal_list: list): # FIXME: this is not a linear circuit
        """apply gain and noise to input signal

        Args:
            input_signal_list: a list of input signals to maximum voltage.

        Returns:
            2D/3D tensor: maximum signal after maximum voltage.
        """
        input_shape = input_signal_list[0].shape

        for input_signal in input_signal_list:
            if input_signal.shape != input_shape:
                raise Exception("In 'MaximumVoltageFunc', input signal shapes in list are not consistent!")

        max_signal = np.zeros(input_shape)

        for input_signal in input_signal_list:
            max_signal = np.maximum(input_signal, max_signal)

        max_after_noise = self.rs.normal(
            scale = self.noise,
            size = input_shape
        ) + max_signal

        return max_after_noise

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class PixelwiseFunc(object):
    """A general interface for pixelwise noise

    A general interface for any noise source resided inside each pixel,
    including floating diffusion, source follower, etc. General assumption of the noise source
    is that the noise follows a "zero-mean" Gaussian distribution. Users need to provide mean 
    noise (sigma value).

    Mathematical Expression:
        out = (gain * in) + Norm(noise)

    Args:
        name (str): the name of the noise.
        gain (float): the average gain. Default value is ``1.0``.
        noise (float): the standard deviation of read noise. Default value is ``None``.
        enable_prnu (bool): flag to enable PRNU. Default value is ``False``.
        prnu_std (float): the relative prnu standard deviation respect to gain.
                  prnu gain standard deviation = prnu_std * gain.
                  the default value is ``0.001``.
    """
    def __init__(
        self,
        name,
        gain = 1.0,
        noise = None,
        enable_prnu = False,
        prnu_std = 0.001
    ):
        super(PixelwiseFunc, self).__init__()
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

    def simulate_output(self, input_signal):
        """apply gain and noise to input signal

        Args:
            input_signal: the input signals.

        Returns:
            2D/3D tensor: signal values after processed by analog compoenent.
        """
        input_shape = input_signal.shape
        if self.enable_prnu:
            if self.prnu_gain is None or self.prnu_gain.shape != input_signal.shape:
                self.prnu_gain = self.rs.normal(
                    loc = self.gain,
                    scale = self.gain * self.prnu_std,
                    size = input_shape
                )
            # generate random gain values
            input_after_gain = self.prnu_gain * input_signal
        else:
            input_after_gain = self.gain * input_signal

        input_after_noise = self.rs.normal(
            scale = self.noise,
            size = input_shape
        ) + input_after_gain

        return input_after_noise

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class FloatingDiffusionFunc(object):
    """A noise model for floating diffusion

    General assumption of the noise model is that the noise follows a ``zero-mean``
    Gaussian distribution. Users need to provide the average noise error (sigma value).
    Gain is generally slightly less than 1, here, the default value is 1.0.

    To enable CDS and PRNU, just set enable flag to be True. If ``enable_cds`` is True,
    simulate_output function will return two values, one is the input + reset noise, 
    and the other is the reset noise.

    Mathematical Expression:
        out = (gain * in) + Norm(noise)

    Args:
        name (str): the name of the noise.
        gain (float): the average gain. Default value is ``1.0``.
        noise (float): the standard deviation of read noise. Default value is ``None``.
        enable_cds (bool): flag to enable CDS (correlated double sampling). Default value is ``False``.
        enable_prnu (bool): flag to enable PRNU. Default value is ``False``.
        prnu_std (float): the relative prnu standard deviation respect to gain.
                  prnu gain standard deviation = prnu_std * gain. the default value is ``0.001``.
    """
    def __init__(
        self,
        name: str,
        gain = 1.0,
        noise = None,
        enable_cds = False,
        enable_prnu = False,
        prnu_std = 0.001

    ):
        super(FloatingDiffusionFunc, self).__init__()
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

    def simulate_output(self, input_signal):
        """apply gain and noise to input signal

        Args:
            input_signal: the input signals.

        Returns:
            2D/3D tensor: signal values after processed by floating diffusion. If ``enable_cds`` is
            ``True``, then the second return value is reset noise.
        """       
        input_shape = input_signal.shape
        if self.enable_prnu:
            if self.prnu_gain is None or self.prnu_gain.shape != input_signal.shape:
                self.prnu_gain = self.rs.normal(
                    loc = self.gain,
                    scale = self.gain * self.prnu_std,
                    size = input_shape
                )
            # generate random gain values
            input_after_gain = self.prnu_gain * input_signal
        else:
            input_after_gain = self.gain * input_signal

        reset_noise = self.rs.normal(
            scale = self.noise,
            size = input_shape
        )
        input_after_noise = reset_noise + input_after_gain

        if self.enable_cds:
            return input_after_noise, reset_noise
        else:
            return input_after_noise

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class CorrelatedDoubleSamplingFunc(object):
    """A noise model for correlated double sampling module.

    General assumption of CDS is gain is 1, read noise follows ``zero-mean`` normal distribution.

    Mathematical Expression:
        output = (input_signal - reset_signal) * gain + Norm(noise)

    Args:
        name (str): the name of the noise.
        gain (float): the average gain. Default value is ``1.0``.
        noise (float): the standard deviation of read noise. Default value is ``None``.
        enable_prnu: flag to enable PRNU. Default value is ``False``.
        prnu_std: the relative prnu standard deviation respect to gain.
                  prnu gain standard deviation = prnu_std * gain. The default value is ``0.001``.
        
    """
    def __init__(
        self,
        name: str,
        gain = 1,
        noise = None,
        enable_prnu = False,
        prnu_std = 0.001
    ):
        super(CorrelatedDoubleSamplingFunc, self).__init__()
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

    def simulate_output(self, input_signal, reset_noise):
        """apply gain and noise to input signal

        Args:
            input_signal: the input signals.
            reset_noise: reset noise signal from floating diffusion.

        Returns:
            2D/3D tensor: signal values after processed by CDS.
        """ 
        if input_signal.shape != reset_noise.shape:
            raise Exception("input_signal and reset_noise need to be the same shape in 'CorrelatedDoubleSamplingFunc'")
                
        input_shape = input_signal.shape

        input_diff = input_signal - reset_noise

        if self.enable_prnu:
            if self.prnu_gain is None or self.prnu_gain.shape != input_signal.shape:
                self.prnu_gain = self.rs.normal(
                    loc = self.gain,
                    scale = self.gain * self.prnu_std,
                    size = input_shape
                )
            # generate random gain values
            input_after_gain = self.prnu_gain * input_diff
        else:
            input_after_gain = self.gain * input_diff


        input_after_noise = self.rs.normal(
            scale = self.noise,
            size = input_shape
        ) + input_after_gain

        return input_after_noise

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class ComparatorFunc(object):
    """Comparator noise model

    The general assumption for comparator component is that its gain is 1,
    and its noise follows zero-mean normal distribution.

    Mathematical Expression:
        output = GreaterThanOne(Diff(input_signal1 - input_signal2) * gain + Norm(noise))

    Args:
        name (str): the name of the noise.
        gain (float): the average gain. Default value is ``1.0``.
        noise (float): the standard deviation of read noise. Default value is ``None``.
        enable_prnu (bool): flag to enable PRNU. Default value is ``False``.
        prnu_std (float): the relative PRNU standard deviation respect to gain.
            PRNU gain standard deviation = prnu_std * gain. The default value is 0.001
    """
    def __init__(
        self,
        name,
        gain = 1.0,
        noise = None,
        enable_prnu = False,
        prnu_std = 0.001
    ):
        super(ComparatorFunc, self).__init__()
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

    def simulate_output(self, input_signal1, input_signal2):
        """apply gain and noise to input signals.

        Args:
            input_signal1: the first input signal.
            input_signal2: the second input signal.

        Returns:
            2D/3D tensor: signal values in ``input_signal1`` that are greater that corresponding values in ``input_signal2``. Otherwise, output zeros.
        """ 
        if input_signal1.shape != input_signal2.shape:
            raise Exception("two inputs to 'ComparatorFunc' should be in the same shape.")

        input_shape = input_signal1.shape
        input_diff = input_signal1 - input_signal2
        
        if self.enable_prnu:
            if self.prnu_gain is None or self.prnu_gain.shape != input_signal.shape:
                self.prnu_gain = self.rs.normal(
                    loc = self.gain,
                    scale = self.gain * self.prnu_std,
                    size = input_shape
                )
            # generate random gain values
            input_after_gain = self.prnu_gain * input_diff
        else:
            input_after_gain = self.gain * input_diff

        input_after_noise = self.rs.normal(
            scale = self.noise,
            size = input_shape
        ) + input_after_gain

        # find value less than 0 and mask them 0.
        result = copy.deepcopy(input_signal1)
        result[input_after_noise<0] = 0

        return result

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class ColumnwiseFunc(object):
    """A general interface for column-wise noise

    A general interface for any noise source that applies to
    each column, such as column amplifier. Assumption for this class is that 
    it has a row-like struction such as column amplifier, and this class can 
    capture the different properties in columnwise structure. One example is 
    the column amplifier has PRNU columnwise.

    Mathematical Expression:
        output = gain * in + Norm(noise)

    Args:
        name (str): the name of the noise.
        gain (float): the average gain. Default value is ``1.0``.
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
        name,
        gain = 1.0,
        noise = None,
        enable_prnu = False,
        prnu_std = 0.001,
        enable_offset = False,
        pixel_offset_voltage = 0.1,
        col_offset_voltage = 0.05,
    ):
        super(ColumnwiseFunc, self).__init__()
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

    def simulate_output(self, input_signal):
        """apply gain and noise to input signal

        Args:
            input_signal: the input signals.

        Returns:
            2D/3D tensor: signal values after processed by columnwise noise component.
        """  
        if len(input_signal.shape) != 3:
            raise Exception("input signal in noise model needs to be in (height, width, channel) 3D shape.")
                
        input_height, input_width, input_channel = input_signal.shape
        if self.enable_offset:
            input_signal += self.pixel_offset_voltage
        if self.enable_prnu:
            if self.prnu_gain is None or self.prnu_gain.shape != input_signal.shape:
                self.prnu_gain = np.repeat(
                    np.repeat(
                        self.rs.normal(
                            loc = self.gain,
                            scale = self.gain * self.prnu_std,
                            size = (1, input_width, 1)
                        ),
                        input_height,
                        axis = 0
                    ),
                    input_channel,
                    axis = 2
                )
            # generate random gain values
            input_after_gain = self.prnu_gain * input_signal
        else:
            input_after_gain = self.gain * input_signal

        input_after_noise = self.rs.normal(
            scale = self.noise,
            size = (input_height, input_width, input_channel)
        ) + input_after_gain

        if self.enable_offset:
            input_after_gain += self.col_offset_voltage

        return input_after_noise

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


