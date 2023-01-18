import numpy as np
import math
import os
import cv2
import time
import random
import tensorflow as tf


from noise_model import Photodiode, ADCQuantization, PixelwiseComponent,\
					ColumnwiseComponent, FloatingDiffusion, CorrelatedDoubleSampling
from reverse_process import unprocess
from forward_process import process, process_only_gain, process_no_demosaic
from isp_utils import convert_raw, convert_bayer, edge_aware_demosaic, \
					  luminance_based_demosaic, chroma_filter_demosaic
def main():

	# sensor specs
	full_scale_input_voltage = 2.7 # V
	pixel_full_well_capacity = 10000 # e

	# noise specs
	conversion_gain = 2.7/10000./2.
	column_amplifier_gain = 2.0
	column_amplifier_noise_pct = 0.05
	dc_noise = 2.5 # electrons
	fd_read_noise = 0.02 # V
	sf_read_noise = 0.01 # V
	cds_noise = 0.01 # V
	adc_noise = 0.02 # V
	pixel_offset_voltage = 0.1 # V
	col_offset_voltage = 0.05 # V
	
	adc_resolution = 8 # bits

	# create noise objects
	pd_noise = Photodiode(
		"Photodiode",
		dark_current_noise=dc_noise,
		max_val=pixel_full_well_capacity,
		enable_dcnu=True,
		dcnu_percentage=0.05,
	)

	fd_noise = FloatingDiffusion(
		name = "FloatingDiffusion",
		gain = conversion_gain,
		noise = fd_read_noise,
		max_val = pixel_full_well_capacity*conversion_gain,
		enable_cds = True,
		enable_prnu = True,
	)

	sf_noise = PixelwiseComponent(
		name = "SourceFollower",
		gain = 1.0,
		noise = sf_read_noise,
		max_val = pixel_full_well_capacity*conversion_gain,
	)

	col_amplifier_noise = ColumnwiseComponent(
		name = "ColumnAmplifier",
		gain = column_amplifier_gain,
		max_val = pixel_full_well_capacity*conversion_gain*column_amplifier_gain,
		noise_percentage = column_amplifier_noise_pct,
		enable_prnu = True
	)

	cds_noise = CorrelatedDoubleSampling(
		name = "CorrelatedDoubleSampling",
		noise = cds_noise,
		max_val = pixel_full_well_capacity*conversion_gain*column_amplifier_gain,
	)

	adc_noise = ADCQuantization(
		name = "ADCQuantization",
		adc_noise = adc_noise,
		max_val = pixel_full_well_capacity*conversion_gain*column_amplifier_gain
	)

	# file dir
	dir_path = "val2017"
	output_dir_path = "noise_%s" % dir_path
	img_files = os.listdir(dir_path)

	os.makedirs(output_dir_path, exist_ok=True)

	for fn in img_files[:10]:
		img_name = "%s/%s" % (dir_path, fn)
		print("processing %s" % (img_name))
		# load test image
		org_img = np.array(cv2.imread(img_name, cv2.IMREAD_COLOR), dtype=np.float32)/255.

		# trim the image to be multiple of 2
		(H, W, _) = org_img.shape
		org_img = org_img[:(H//2)*2, :(W//2)*2, :]

		# convert to tensor for tf reverse process
		org_img = tf.convert_to_tensor(org_img, dtype=tf.float32)

		# reverse process and generate raw bayer image (H//2, W//2, 4)
		# 4 is for RGGB
		# print("org img: ", org_img.shape)
		bayer_raw, metadata = unprocess(org_img)
		# convert bayer image to raw image (H, W)
		raw_img = convert_raw(bayer_raw)

		# a simple inverse img to photon
		photon_input = raw_img/1.0*pixel_full_well_capacity

		# apply shot noise and dark current noise
		signal_after_pd_noise = pd_noise.apply_gain_and_noise(photon_input)
		# apply fd noise
		voltage_after_fd_noise, reset_voltage = fd_noise.apply_gain_and_noise(signal_after_pd_noise)
		# apply sf noise
		voltage_after_sf_noise = sf_noise.apply_gain_and_noise(voltage_after_fd_noise)
		reset_voltage = sf_noise.apply_gain_and_noise(reset_voltage)
		# apply col ampifier noise
		voltage_after_col_amp_noise = col_amplifier_noise.apply_gain_and_noise(voltage_after_sf_noise)
		reset_voltage = col_amplifier_noise.apply_gain_and_noise(reset_voltage)
		# apply cds noise
		voltage_after_cds_noise = cds_noise.apply_gain_and_noise(voltage_after_col_amp_noise, reset_voltage)
		# apply adc quantization
		img_after_adc = adc_noise.apply_gain_and_noise(voltage_after_col_amp_noise)
		# covert back to raw
		noise_raw = (img_after_adc/full_scale_input_voltage*255).astype(np.uint8)
		# cv2.imshow("noise raw", img_after_adc/np.max(img_after_adc))
		# cv2.waitKey(0)
		# cv2.destroyAllWindows()

		noise_bayer = convert_bayer(noise_raw)/255.

		noise_bayer = tf.convert_to_tensor(noise_bayer, dtype=tf.float32)

		restored_img = chroma_filter_demosaic(noise_bayer, metadata)
		restored_img = np.clip(restored_img, 0, 1)
		# cv2.imshow("restored_img", restored_img)
		# cv2.waitKey(0)
		# cv2.destroyAllWindows()
		cv2.imwrite("%s/%s" % (output_dir_path, fn), restored_img*255)


if __name__ == '__main__':
	main()


