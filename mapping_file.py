def mapping_function_case3():
    mapping = {
        "ImageCapture": "PixelArray",
        "CDS": "ConvCircuit_1",

        "Conv2D_1": "ConvCircuit_1",
        "MaxPooling_1": "MPCircuit_1",
        "ReLU_1": "MPCircuit_1",
        "Conv2D_2": "ConvCircuit_2",
        "MaxPooling_2": "MPCircuit_2",
        "ReLU_2": "MPCircuit_2",

        "Quantization": "ADC",

        "FC": "DigitalProcessor"
    }

    return mapping
