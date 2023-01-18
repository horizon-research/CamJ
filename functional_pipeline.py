import numpy as np
import math
import cv2
import time

from noise_model import Photodiode, ADCQuantization, PixelwiseComponent,\
					ColumnwiseComponent, FloatingDiffusion, CorrelatedDoubleSampling

def main():

	img_name = "test_img.jpeg"
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

	# load test image
	org_img = np.array(cv2.imread(img_name, cv2.IMREAD_GRAYSCALE))
	
	# a simple inverse img to photon
	photon_input = org_img/np.max(org_img)*pixel_full_well_capacity

	# create noise objects
	pd_noise = Photodiode(
		"Photodiode",
		dark_current_noise=dc_noise,
		max_val=pixel_full_well_capacity,
		enable_dcnu=True,
		dcnu_percentage=0.05,
	)

	signal_after_pd_noise = pd_noise.apply_gain_and_noise(photon_input)

	print("image after shot noise, max: ", np.max(signal_after_pd_noise))
	cv2.imshow("image after shot noise", signal_after_pd_noise/np.max(signal_after_pd_noise))
	cv2.waitKey(0)
	cv2.destroyAllWindows()

	fd_noise = FloatingDiffusion(
		name = "FloatingDiffusion",
		gain = conversion_gain,
		noise = fd_read_noise,
		max_val = pixel_full_well_capacity*conversion_gain,
		enable_cds = True,
		enable_prnu = True,
	)

	voltage_after_fd_noise, reset_voltage = fd_noise.apply_gain_and_noise(signal_after_pd_noise)

	print("image after fd noise, max: ", np.max(voltage_after_fd_noise))
	cv2.imshow("image after fd noise", voltage_after_fd_noise/np.max(voltage_after_fd_noise))
	cv2.waitKey(0)
	cv2.destroyAllWindows()

	sf_noise = PixelwiseComponent(
		name = "SourceFollower",
		gain = 1.0,
		noise = sf_read_noise,
		max_val = pixel_full_well_capacity*conversion_gain,
	)

	voltage_after_sf_noise = sf_noise.apply_gain_and_noise(voltage_after_fd_noise)
	reset_voltage = sf_noise.apply_gain_and_noise(reset_voltage)

	print("image after sf noise, max: ", np.max(voltage_after_sf_noise))

	col_amplifier_noise = ColumnwiseComponent(
		name = "ColumnAmplifier",
		gain = column_amplifier_gain,
		max_val = pixel_full_well_capacity*conversion_gain*column_amplifier_gain,
		noise_percentage = column_amplifier_noise_pct,
		enable_prnu = True
	)

	voltage_after_col_amp_noise = col_amplifier_noise.apply_gain_and_noise(voltage_after_sf_noise)
	reset_voltage = col_amplifier_noise.apply_gain_and_noise(reset_voltage)

	print("voltage_after_col_amp_noise", np.max(voltage_after_col_amp_noise))
	cv2.imshow(
		"image after col amplifier noise", 
		voltage_after_col_amp_noise/np.max(voltage_after_col_amp_noise)
	)
	cv2.waitKey(0)
	cv2.destroyAllWindows()

	cds_noise = CorrelatedDoubleSampling(
		name = "CorrelatedDoubleSampling",
		noise = cds_noise,
		max_val = pixel_full_well_capacity*conversion_gain*column_amplifier_gain,
	)
	voltage_after_cds_noise = cds_noise.apply_gain_and_noise(voltage_after_col_amp_noise, reset_voltage)

	print("image after cds noise, max: ", np.max(voltage_after_cds_noise))
	cv2.imshow(
		"image after cds noise", 
		voltage_after_cds_noise/np.max(voltage_after_cds_noise)
	)
	cv2.waitKey(0)
	cv2.destroyAllWindows()

	adc_noise = ADCQuantization(
		name = "ADCQuantization",
		adc_noise = adc_noise,
		max_val = pixel_full_well_capacity*conversion_gain*column_amplifier_gain
	)

	img_after_adc = adc_noise.apply_gain_and_noise(voltage_after_col_amp_noise)
	print("image after adc, max: ", np.max(img_after_adc))
	img_after_adc = (img_after_adc/full_scale_input_voltage*255).astype(np.uint8)


	cv2.imshow("image after adc", img_after_adc/np.max(img_after_adc))
	cv2.waitKey(0)
	cv2.destroyAllWindows()

	cv2.imwrite("noise_raw2.png", img_after_adc)


if __name__ == '__main__':
	main()


