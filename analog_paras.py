# define operator-wise energy (pJ), delay (cycles) and area (um^2)
# hardware reuse should be considered

import numpy as np


class Energy:
    def __init__(self):
        pass

    def read(self):
        return 0

    def write(self):
        return 0


class Delay:
    def __init__(self):
        pass

    def read(self):
        return 0

    def write(self):
        return 0


class Area:
    def __init__(self):
        pass

    def read(self, reuse_factor):
        return 0 * reuse_factor

    def write(self, reuse_factor):
        return 0 * reuse_factor
