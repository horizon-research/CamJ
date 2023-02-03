import numpy as np


def gm_id(load_capacitance,
          gain,
          bandwidth,
          differential=True,
          inversion_level='moderate'):
    if inversion_level == 'strong':
        gm_id_ratio = 10
    elif inversion_level == 'moderate':
        gm_id_ratio = 15
    elif inversion_level == 'weak':
        gm_id_ratio = 20
    num_branch = np.where(differential, 2, 1)
    gm = 2 * np.pi * load_capacitance * gain * bandwidth
    id = gm / gm_id_ratio * num_branch * 1e9  # [nA]

    return id


def get_pixel_parasitic(array_v,
                        tech_node,  # [nm]
                        pitch  # [um]
                        ):
    C_p = 9e-15 / 130 / 5 * tech_node * pitch * array_v
    return C_p


def get_nominal_supply(tech_node):
    if 130 < tech_node <= 180:
        supply = 1.8
    if 65 < tech_node <= 130:
        supply = 1.5
    if tech_node <= 65:
        supply = 1.1
    else:
        raise Exception("Defined tech_node is not supported.")
    return supply
