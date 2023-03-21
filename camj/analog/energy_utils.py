import numpy as np

def gm_id(
        load_capacitance,
        gain,
        bandwidth, # [Hz]
        differential=True,
        inversion_level='moderate'
    ):
    """ Compute transconductance (gm) and drain current (id) of linear amplifiers.

        The method is based on "(2017, CAMBRIDGE) SYSTEMATIC DESIGN OF ANALOG CMOS CIRCUITS -- Using Pre-Computed Lookup Tables".

        Args:
            load_capacitance (float): amplifier's load capacitance.
            gain (float): amplifier's open-loop gain.
            bandwidth (float): amplifier's bandwidth.
            differential (bool): if using differential-input amplifier or single-input amplifier.
            inversion_level (str): 'weak', 'moderate', or 'strong'. It describes the inversion level of the transistors in the amplifier.
    """

    if inversion_level == 'strong':
        gm_id_ratio = 10
    elif inversion_level == 'moderate':
        gm_id_ratio = 16
    elif inversion_level == 'weak':
        gm_id_ratio = 20
    num_branch = np.where(differential, 2, 1)
    gm = 2 * np.pi * load_capacitance * gain * bandwidth
    id = gm / gm_id_ratio * num_branch  # [A]

    return [id, gm]


def get_pixel_parasitic(
        array_v,
        tech_node,  # [nm]
        pitch  # [um]
    ):
    """ Compute parasitic capacitance on the pixel's output node.

        The parasitic capacitance usually dominates the load capacitance if the pixel's readout circuitry is placed beside the pixel array.

        Args:
            array_v (int): vertical size of the pixel array.
            tech_node (int): pixel's process node.
            pitch (float): pixel's pitch size.
    """

    C_p = 9e-15 / 130 / 5 * tech_node * pitch * array_v
    return C_p


def get_nominal_supply(tech_node):
    """ Compute nominal supply voltage under different process nodes.

        Args:
            tech_node (int): pixel's process node.
    """

    if 130 < tech_node <= 180:
        supply = 1.8
    if 65 < tech_node <= 130:
        supply = 1.5
    if tech_node <= 65:
        supply = 1.1
    else:
        raise Exception("Defined tech_node is not supported.")
    return supply


def parallel_impedance(impedance_array):
    impedance = np.reciprocal(np.sum(np.reciprocal(impedance_array)))
    return impedance


def get_delay(
        current_stage_output_impedance,
        next_stage_input_impedance,
        current_stage_output_capacitance,
        next_stage_input_capacitance
    ):
    # 5*Tau represents charging to 99% of the full voltage from 0
    delay = 5 * (parallel_impedance([current_stage_output_impedance, next_stage_input_impedance])) * \
            (current_stage_output_capacitance + next_stage_input_capacitance)
    return delay