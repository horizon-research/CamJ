import numpy as np


class AFS:
    def __init__(self):
        # add universal noise
        pass

    def read(self, x):
        return x

    def write(self, x):
        return x

    def quantization(self, reso, x, x_max):
        return np.round(x / x_max * (2 ** reso - 1)) / (2 ** reso - 1) * x_max
