# JSSC'21

import numpy as np
import hw_config_tianrui as config

# pixel exposure (light -> PWM), three-row-wise
PixelArray = config.PixelArray(size=[128, 128], pitch=7.6, ismonochrome=False)
PixelArray.pixel(type='PWM')
PixelArray.exposure(type='multi_rolling_shutter')

# interface (PWM -> I), DAC-2
Interface_1 = config.Analog_Cell(type=['DAC', 2])
Interface_1.

# MAC, column parallel (I -> V)

# ADC (V -> D), SS ADC
