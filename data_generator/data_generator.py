import numpy as np


def gm_id(load_capacitance,
          gain,
          bandwidth,
          differential=True,
          inversion_level='moderate'):
    if inversion_level == 'weak':
        gm_id_ratio = 20
    elif inversion_level == 'moderate':
        gm_id_ratio = 15
    elif inversion_level == 'strong':
        gm_id_ratio = 10
    num_branch = np.where(differential, 2, 1)
    gm = 2 * np.pi * load_capacitance * gain * bandwidth
    id = gm / gm_id_ratio * num_branch * 1e9  # [nA]

    return id


def get_gain_min(resolution):
    gain_min = 2 ** resolution
    return gain_min


def get_pixel_parasitic(array_v,
                        technology,  # [nm]
                        pitch  # [um]
                        ):
    C_p = 9e-15 / 130 / 5 * technology * pitch * array_v
    return C_p


id = gm_id(load_capacitance=100e-15,
           gain=1,
           bandwidth=28.8e3,
           differential=True,
           inversion_level='strong')
vdd = 1.5
t = 1/90
energy_opamp = vdd * (id * 1e-9) * t * 1e12
print(id)
print(energy_opamp)

vpd = 1.5
vsf = 1.1
energy_pixel = 100e-15 * vpd ** 2 * 1e12 + 100e-15 * vpd ** 2 * 1e12 + (
            get_pixel_parasitic(400, 130, 5) + 100e-15) * vpd * vsf * 1e12
print(energy_pixel)
