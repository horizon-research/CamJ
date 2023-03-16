
def mapping_function():
    mapping = {
        # analog simulation
        "AnalogInput" : "PixelArray",
        "Binning" : "BinningArray",
        "Weight" : "HaarArray",
        "Haar" : "HaarArray",
        # digital simulation
        "Input" : "ADC",
        "Conv2D-1" : "InSensorSystolicArray",
        "Conv2D-2-1" : "InSensorSystolicArray",
        "Conv2D-2-2" : "InSensorSystolicArray",
        "Conv2D-3" : "InSensorSystolicArray",
        "Conv2D-4" : "InSensorSystolicArray",
        "FC-1" : "InSensorSystolicArray",
        "MaxPool-1" : "MPUnit",
        "MaxPool-2" : "MPUnit",
        "MaxPool-3" : "MPUnit",
        "MaxPool-4" : "MPUnit",
    }

    return mapping
