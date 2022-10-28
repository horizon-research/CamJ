import numpy as np


def gm_id(load_capacitance,
          gain,
          bandwidth,
          differential=True,
          inversion_level='moderate'):
    if inversion_level == 'weak':
        gm_id_ratio = 10
    elif inversion_level == 'moderate':
        gm_id_ratio = 15
    elif inversion_level == 'strong':
        gm_id_ratio = 20
    num_branch = np.where(differential, 2, 1)
    gm = 2 * np.pi * load_capacitance * gain * bandwidth
    id = gm / gm_id_ratio * num_branch * 1e9  # [nA]

    return id


def get_gain_min(resolution):
    gain_min = 2 ** resolution
    return gain_min
