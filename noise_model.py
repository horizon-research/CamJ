import numpy as np
import math
import cv2
import time

class Photodiode(object):
	"""docstring for Photodiode"""
	def __init__(self, 
		name,
		dark_current_noise,
		enable_dcnu=False,
		dcnu_percentage=0.05,
	):
		super(Photodiode, self).__init__()
		self.name = name
		self.dark_current_noise = dark_current_noise
		self.enable_dcnu = enable_dcnu
		self.dcnu_percentage = dcnu_percentage

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
			signal_after_dc_noise = self.rs.poisson(
				self.dark_current_noise, 
				size=(input_height, input_width)
			) + signal_after_shot_noise
		else:
			# first generate dcnu variant for each pixel
			dcnu_noise = self.rs.normal(
				loc = self.dark_current_noise,
				scale = self.dark_current_noise*self.dcnu_percentage,
				size = (input_height, input_width)
			)
			# then apply poisson distrobution on dcnu
			signal_after_dc_noise = self.rs.poisson(
				dcnu_noise, 
				size=(input_height, input_width)
			) + signal_after_shot_noise

		return np.clip(signal_after_dc_noise, a_min=0, a_max=np.max(input_signal))

	def __str__(self):
		return self.name

	def __repr__(self):
		return self.name

class ADCQuantization(object):
	"""docstring for ADCQuantization"""
	def __init__(
		self, 
		name,
		adc_noise
	):
		super(ADCQuantization, self).__init__()
		self.name = name
		self.adc_noise = adc_noise

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

		return np.clip(signal_after_noise, a_min=0, a_max=np.max(input_signal))

	def __str__(self):
		return self.name

	def __repr__(self):
		return self.name

class PixelwiseComponent(object):
	"""
		A general interface for any noise source resided inside each pixel,
		including floating diffusion, source follower, etc.

		General assumption of the noise source is that the noise 
		follows a "zero-mean" Gaussian distribution. Users need 
		to provide either noise error (sigma value) or a error
		percentage rate which is applied to the input signal:
		sigma = percentage rate * input signal

		If noise parameter exists, noise_percentage will be ignored.

		Order: gain will be first applied before adding noises.
	"""
	def __init__(
		self,
		name,
		gain=1,
		noise=None,
		noise_percentage=None,
		enable_prnu=False,
		prnu_percentage=0.02

	):
		super(PixelwiseComponent, self).__init__()
		self.name = name
		self.gain = gain
		self.noise = noise
		self.noise_percentage = noise_percentage
		self.enable_prnu = enable_prnu
		self.prnu_percentage = prnu_percentage

		if self.noise == None and self.noise_percentage == None:
			raise Exception("Insufficient parameters: noise and noise_percentage both are None.")

		# initialize random number generator
		random_seed = int(time.time())
		self.rs = np.random.RandomState(random_seed)

	def apply_gain_and_noise(self, input_signal):
		if len(input_signal.shape) != 2:
			raise Exception("input signal in noise model needs to be in (height, width) 2D shape.")
				
		input_height, input_width = input_signal.shape
		if self.enable_prnu:
			# generate random gain values
			input_after_gain = self.rs.normal(
				loc = self.gain,
				scale = self.gain*self.prnu_percentage,
				size = (input_height, input_width)
			) * input_signal
		else:
			input_after_gain = self.gain * input_signal

		if self.noise is not None:
			input_after_noise = self.rs.normal(
				scale = self.noise,
				size = (input_height, input_width)
			) + input_after_gain
		elif self.noise_percentage is not None:
			# print((self.noise_percentage * input_signal).shape)
			input_after_noise = self.rs.normal(
				scale = self.noise_percentage * input_signal,
				size = (input_height, input_width)
			) + input_after_gain
		else:
			raise Exception("Insufficient parameters: noise and noise_percentage both are None.")

		return np.clip(input_after_noise, a_min=0, a_max=np.max(input_signal)*self.gain)

	def __str__(self):
		return self.name

	def __repr__(self):
		return self.name

class ColumnwiseComponent(object):
	"""
		A general interface for any noise source that applies to
		each column, such as column amplifier.

		Order: gain will be first applied before adding noises.
	"""
	def __init__(
		self,
		name,
		gain=1,
		noise=None,
		noise_percentage=None,
		enable_prnu=False,
		prnu_percentage=0.01,
		enable_offset=False,
		pixel_offset_voltage=0.1,
		col_offset_voltage=0.05
	):
		super(ColumnwiseComponent, self).__init__()
		self.name = name
		self.gain = gain
		self.noise = noise
		self.noise_percentage = noise_percentage
		self.enable_prnu = enable_prnu
		self.prnu_percentage = prnu_percentage
		self.enable_offset = enable_offset
		self.pixel_offset_voltage = pixel_offset_voltage
		self.col_offset_voltage = col_offset_voltage

		if self.noise == None and self.noise_percentage == None:
			raise Exception("Insufficient parameters: noise and noise_percentage both are None.")

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
			# generate random gain values
			input_after_gain = np.repeat(
				self.rs.normal(
					loc = self.gain,
					scale = self.gain*self.prnu_percentage,
					size = (1, input_width)
				),
				input_height,
				axis=0
			) * input_signal
		else:
			input_after_gain = self.gain * input_signal

		if self.noise is not None:
			input_after_noise = self.rs.normal(
				scale = self.noise,
				size = (input_height, input_width)
			) + input_after_gain
		elif self.noise_percentage is not None:
			# print((self.noise_percentage * input_signal).shape)
			input_after_noise = self.rs.normal(
				scale = self.noise_percentage * input_signal,
				size = (input_height, input_width)
			) + input_after_gain
		else:
			raise Exception("Insufficient parameters: noise and noise_percentage both are None.")

		if self.enable_offset:
			input_after_gain += self.col_offset_voltage

		return np.clip(input_after_noise, a_min=0, a_max=np.max(input_signal)*self.gain)

	def __str__(self):
		return self.name

	def __repr__(self):
		return self.name


