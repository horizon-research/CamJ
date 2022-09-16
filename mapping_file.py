def mapping_function():
    mapping = {
        "CurrInput": "ADC",
        "PrevInput": "ADC",

        "BBoxFinding": "BBoxDetection",
        "EdgeDetection": "EdgeDetection",
        "Thresholding": "Thresholding",
        "Eventification": "Eventification",

        "Conv2D_1": "InSensorSystolicArray",
        "Conv2D_2": "InSensorSystolicArray",
        "Conv2D_3": "InSensorSystolicArray",
        "FC_1": "InSensorSystolicArray",
        "FC_2": "InSensorSystolicArray",

        "EncoderDecoder": "NearSensorSystolicArray"
    }

    return mapping
