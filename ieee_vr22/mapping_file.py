
def mapping_function():
	mapping = {
		"CurrInput" : "ADC",
		"PrevInput" : "ADC",
		
		"CurrResize" : "ResizeUnit",
		"PrevResize" : "ResizeUnit",

		"Thresholding" : "ThresholdingUnit",
		"Eventification" : "Eventification",

		"Conv2D_1" : "InSensorSystolicArray",
		"Conv2D_2" : "InSensorSystolicArray",
		"Conv2D_3" : "InSensorSystolicArray",
		"FC_1" : "InSensorSystolicArray",
		"FC_2" : "InSensorSystolicArray",

	}

	return mapping

def mapping_function_w_analog():
	mapping = {
		# analog computing
		"CurrInput" : "PixelArray",
		"CurrResize" : "PixelArray",
		"PrevResizedInput" : "AnalogMemoryArray",
		"Eventification" : "EventificationArray",

		# digital computing
		"Thresholding" : "ThresholdingUnit",
		"Conv2D_1" : "InSensorSystolicArray",
		"Conv2D_2" : "InSensorSystolicArray",
		"Conv2D_3" : "InSensorSystolicArray",
		"FC_1" : "InSensorSystolicArray",
		"FC_2" : "InSensorSystolicArray",
	}

	return mapping