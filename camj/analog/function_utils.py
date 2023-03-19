from inspect import signature

def process_signal_stage(stage, input_signals):

    output_signals = []
    sig = signature(stage.apply_gain_and_noise)
    
    if len(sig.parameters) == 1:
        for input_signal in input_signals:
            output_signal = stage.apply_gain_and_noise(input_signal)
            if isinstance(output_signal, tuple):
                for item in output_signal:
                    output_signals.append(item)
            else:
                output_signals.append(output_signal)
    elif len(sig.parameters) == 2:
        if len(input_signals) != 2:
            raise Exception("Input for this stage needs to be 2!")
        output_signal = stage.apply_gain_and_noise(input_signals[0], input_signals[1])
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