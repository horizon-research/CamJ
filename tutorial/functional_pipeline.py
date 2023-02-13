from functional_core.noise_model import PhotodiodeNoise, ADCQuantization, AbsoluteDifferenceNoise,\
					PixelwiseNoise, FloatingDiffusionNoise, CorrelatedDoubleSamplingNoise, \
					ComparatorNoise, ColumnwiseNoise


def sensor_functional_pipeline():
	# sensor specs
	full_scale_input_voltage = 1.2 # V
	
	# PD parameters
	dc_noise = 2.5 # electrons
	pixel_full_well_capacity = 10000 # e
	dcnu_std = 0.001

	# noise specs
	column_amplifier_gain = 2.0

	# FD parameters
	conversion_gain = full_scale_input_voltage/10000./column_amplifier_gain
	fd_read_noise = 0.002 # V
	fd_prnu_std = 0.001
	# SF parameters
	sf_read_noise = 0.0007 # V
	sf_gain = 1.0
	sf_prnu_std = 0.001 
	# column ampilifer
	col_amp_prnu_std = 0.001
	col_amp_read_noise = 0.002 # V
	# cds
	cds_gain = 1
	cds_noise = 0.001 # V
	cds_std = 0.001


	pixel_offset_voltage = 0.1 # V
	col_offset_voltage = 0.05 # V
	adc_noise = 0.001 # V
	adc_resolution = 8 # bits

	functional_pipeline_list = []

	# create noise objects
	pd_noise = PhotodiodeNoise(
		"Photodiode",
		dark_current_noise=dc_noise,
		max_val=pixel_full_well_capacity,
		enable_dcnu=True,
		dcnu_std=dcnu_std,
	)
	functional_pipeline_list.append(pd_noise)

	fd_noise = FloatingDiffusionNoise(
		name = "FloatingDiffusion",
		gain = conversion_gain,
		noise = fd_read_noise,
		max_val = pixel_full_well_capacity*conversion_gain,
		enable_cds = True,
		enable_prnu = True,
		prnu_std = fd_prnu_std
	)
	functional_pipeline_list.append(fd_noise)

	sf_noise = PixelwiseNoise(
		name = "SourceFollower",
		gain = sf_gain,
		noise = sf_read_noise,
		max_val = pixel_full_well_capacity*conversion_gain,
		enable_prnu = True,
		prnu_std = sf_prnu_std
	)
	functional_pipeline_list.append(sf_noise)

	col_amplifier_noise = ColumnwiseNoise(
		name = "ColumnAmplifier",
		gain = column_amplifier_gain,
		noise = col_amp_read_noise,
		max_val = pixel_full_well_capacity*conversion_gain*column_amplifier_gain,
		enable_prnu = True,
		prnu_std = col_amp_prnu_std
	)
	functional_pipeline_list.append(col_amplifier_noise)

	cds_noise = CorrelatedDoubleSamplingNoise(
		name = "CorrelatedDoubleSampling",
		gain = cds_gain,
		noise = cds_noise,
		max_val = pixel_full_well_capacity*conversion_gain*column_amplifier_gain,
		enable_prnu = True,
		prnu_std = 0.001
	)
	functional_pipeline_list.append(cds_noise)

	adc_noise = ADCQuantization(
		name = "ADCQuantization",
		adc_noise = adc_noise,
		max_val = pixel_full_well_capacity*conversion_gain*column_amplifier_gain
	)
	functional_pipeline_list.append(adc_noise)

	return functional_pipeline_list
