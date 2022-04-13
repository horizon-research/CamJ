import numpy as np


# interface to support ReRAM and CIM
# delay unit: clock cycles
# energy unit: pJ

class AFS:
    def __init__(self):
        # define universal noise, noise can be equivalent to ENOB and SNR
        # define NoC
        pass

    def read(self, x):
        delay = 0
        energy = 0
        return x, delay, energy

    def write(self, x):
        delay = 0
        energy = 0
        return x, delay, energy

    def scaling(self, factor, x):
        delay = 0
        energy = 0
        return factor * x, delay, energy

    def add(self, x1, x2):
        delay = 0
        energy = 0
        return x1 + x2, delay, energy

    def subtract(self, x1, x2):
        delay = 0
        energy = 0
        return x1 - x2, delay, energy

    def multiply(self, x1, x2):
        delay = 0
        energy = 0
        return x1 * x2, delay, energy

    def divide(self, x1, x2):
        delay = 0
        energy = 0
        return x1 / x2, delay, energy

    def AMSmultiply(self, reso, w, w_max, x):
        delay = 0
        energy = 0
        return self.quantization(reso, w, w_max) * x, delay, energy

    def max(self, x1, x2):
        delay = 0
        energy = 0
        return np.maximum(x1, x2), delay, energy

    def min(self, x1, x2):
        delay = 0
        energy = 0
        return np.minimum(x1, x2), delay, energy

    def quantization(self, reso, x, x_max):
        delay = 0
        energy = 0
        return np.round(x / x_max * (2 ** reso - 1)) / (2 ** reso - 1) * x_max, delay, energy

    def threshold(self, x, type):
        y = 0
        if type == 'sign':
            y = np.sign(x)
            delay = 0
            energy = 0
        if type == 'min':
            y = np.min(x)
            delay = 0
            energy = 0
        if type == 'max':
            y = np.max(x)
            delay = 0
            energy = 0
        if type == 'mean':
            y = np.mean(x)
            delay = 0
            energy = 0
        if type == 'sigmoid':
            y = 1 / (1 + np.exp(-x))
            delay = 0
            energy = 0
        if type == 'relu':
            y = x * (x > 0)
            delay = 0
            energy = 0
        if type == 'accumulate':
            y = np.sum(x)
            delay = 0
            energy = 0
        return y, delay, energy

    def commu_intraPE(self, x):
        delay = 0
        energy = 0
        return x, delay, energy
