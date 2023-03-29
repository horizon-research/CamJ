from inspect import signature
from math import sqrt

# import local modules
from camj.general.flags import OP_TEMP, ELECTRON_CHARGE, K_B

def _cap_thermal_noise(capacitance):

    return sqrt(K_B * OP_TEMP / capacitance)

def _single_pole_rc_circuit_thermal_noise(num_transistor, inversion_level, capacitance):

    if inversion_level == 'strong':
        gm_id_ratio = 10
    elif inversion_level == 'moderate':
        gm_id_ratio = 16
    elif inversion_level == 'weak':
        gm_id_ratio = 20
    else:
        raise Exception("Defined inversion_level is not supported.")

    return sqrt(num_transistor * ELECTRON_CHARGE / (2 * gm_id_ratio * capacitance))


def process_signal_stage(stage, input_signals):

    output_signals = []
    sig = signature(stage.simulate_output)
    
    if len(sig.parameters) == 1:
        for input_signal in input_signals:
            output_signal = stage.simulate_output(input_signal)
            if isinstance(output_signal, tuple):
                for item in output_signal:
                    output_signals.append(item)
            else:
                output_signals.append(output_signal)
    elif len(sig.parameters) == 2:
        if len(input_signals) != 2:
            raise Exception("Input for this stage needs to be 2!")
        output_signal = stage.simulate_output(input_signals[0], input_signals[1])
        if isinstance(output_signal, tuple):
                for item in output_signal:
                    output_signals.append(item)
        else:
            output_signals.append(output_signal)
    else:
        raise Exception("Incompatible input and processing stage pair!")

    return output_signals

def default_functional_simulation(functional_pipeline_list, input_list):

    curr_input = input_list
    curr_output = []

    for stage in functional_pipeline_list:
        if isinstance(stage, tuple) or isinstance(stage, list):
            for s in stage:
                output_signals = process_signal_stage(s, curr_input)
                for output_signal in output_signals:
                    curr_output.append(output_signal)
        else:
            output_signals = process_signal_stage(stage, curr_input)
            for output_signal in output_signals:
                curr_output.append(output_signal)

        curr_input = curr_output
        curr_output = []

    return curr_input