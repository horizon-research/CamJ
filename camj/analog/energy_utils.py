import numpy as np


def gm_id(
        load_capacitance,
        gain,
        bandwidth,  # [Hz]
        differential=True,
        inversion_level='moderate'
):
    """ Compute transconductance (gm) and drain current (id) of linear amplifiers.

        The method is based on [Book-Jespers].

        Args:
            load_capacitance (float): [unit: F] amplifier's load capacitance.
            gain (float): amplifier's open-loop gain.
            bandwidth (float): [unit: Hz] amplifier's bandwidth.
            differential (bool): if using differential-input amplifier or single-input amplifier.
            inversion_level (str): ['weak', 'moderate', or 'strong'] the inversion level of the transistors in the amplifier.
    
        Returns:
            drain current (id) [unit: A], transconductance (gm) [unit: S]

        References Link:
            Book-Jespers: Systematic Design of Analog CMOS Circuits: Using Pre-Computed Lookup Tables.
            https://www.cambridge.org/core/books/systematic-design-of-analog-cmos-circuits/A07A705132E9DE52749F65EB63565CE0
    """

    if inversion_level == 'strong':
        gm_id_ratio = 10
    elif inversion_level == 'moderate':
        gm_id_ratio = 16
    elif inversion_level == 'weak':
        gm_id_ratio = 20
    else:
        raise Exception("Defined inversion_level is not supported.")
    num_branch = np.where(differential, 2, 1)
    gm = 2 * np.pi * load_capacitance * gain * bandwidth
    id = gm / gm_id_ratio * num_branch  # [A]

    return [id, gm]


def get_pixel_parasitic(
        array_v,
        tech_node,  # [nm]
        pitch  # [um]
):
    """ Compute column parasitic capacitance (Farad per column) on the pixel's output node.

        This parasitic capacitance usually dominates the load capacitance if the pixel's follow-up circuitry (e.g., readout or processing) is placed at the column level.
        Based on [JSSC-2019] where the parasitic capacitance is 9fF/pixel under 130nm process node and 5um pixel pitch,
        this model assumes the parasitic capacitance scales with process node, pixel pitch, and pixel array's vertical size (i.e., the number of pixels in one column).

        Args:
            array_v (int): vertical size of the pixel array.
            tech_node (int): [unit: nm] pixel's process node.
            pitch (float): [unit: um] pixel's pitch size.

        Returns:
            parasitic capacitance [unit: F]

        References Link:
            JSSC-2019: A Data-Compressive 1.5/2.75-bit Log-Gradient QVGA Image Sensor With Multi-Scale Readout for Always-On Object Detection.
            https://ieeexplore.ieee.org/document/8844721
    """

    C_p = 9e-15 / 130 / 5 * tech_node * pitch * array_v
    return C_p


def get_nominal_supply(tech_node):
    """ Compute nominal supply voltage under different process nodes.

        Args:
            tech_node (int): [unit: nm] pixel's process node.

        Returns:
            supply voltage [unit: V]
    """

    if 130 < tech_node <= 180:
        supply = 1.8
    elif 65 < tech_node <= 130:
        supply = 1.5
    elif tech_node <= 65:
        supply = 1.1
    else:
        raise Exception("Defined tech_node is not supported.")
    return supply


def parallel_impedance(impedance_array):
    """ Compute parallel impedance of an array of input impedance.

        Args:
            impedance_array (array, float): [unit: Ohm] input impedance array.

        Returns:
            parallel impedance [unit: Ohm]
    """

    impedance = np.reciprocal(np.sum(np.reciprocal(impedance_array)))
    return impedance


def get_delay(
        current_stage_output_impedance,
        next_stage_input_impedance,
        current_stage_output_capacitance,
        next_stage_input_capacitance
):
    """ Compute analog component delay.

        This model assumes the delay of an analog component is 5 times of the RC constant at the analog component's output node.
        The total impedance (R) is the sum of the output impedance of this analog component and the input impedance of the following analog component.
        The total capacitance (C) is the sum of the output capacitance of this analog component and the input capacitance of the following analog component.
        5 times of the RC constant represents the latency required by charging the total capacitance to 99% of the nodal voltage swing.

        Args:
            current_stage_output_impedance (float): [unit: Ohm] output impedance of the current analog component.
            next_stage_input_impedance (float): [unit: Ohm] output impedance of the next analog component.
            current_stage_output_capacitance (float): [unit: F] output capacitance of the current analog component.
            next_stage_input_capacitance (float): [unit: F] output capacitance of the next analog component.

        Returns:
            delay [unit: s]
    """

    delay = 5 * (parallel_impedance([current_stage_output_impedance, next_stage_input_impedance])) * \
            (current_stage_output_capacitance + next_stage_input_capacitance)
    return delay
