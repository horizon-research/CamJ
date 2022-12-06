# Case study of "A 0.8V Intelligent Vision Sensor with Tiny Convolutional Neural Network and Programmable Weights Using
# Mixed-Mode Processing-in-Sensor Technique for Image Classification", in ISSCC'22.
# https://ieeexplore.ieee.org/document/9731675


import networkx as nx
from acomp_library import *
# import SW_pipeline as sw

# obtain x and w from sw
# derive mismatch from end-accuracy

# Define pixel array and pixel
# pixel exposure (light -> PWM), three-row-wise
Pixel_array = nx.Graph(color_filter='none',
                       BW_input=[3, 126],
                       BW_output=[3, 126]  # output through 3 column bus
                       )
Pixel_array.add_node('pixel',
                     BW_input=[1, 1],
                     batch_input=1,
                     BW_output=[1, 1],
                     duplication=[126, 126],  # [n_row, n_col]
                     domain_input='optical',
                     domain_output='time',
                     energy=PWM(pd_capacitance=10e-12, pd_supply=0.8, ramp_capacitance=1e-12, gate_capacitance=10e-15,
                                num_readout=8).energy()
                     # value_input=x,
                     # value_output=np.random.normal(x, x * x_mismatch),
                     # ideal_output=x
                     )

# Define weight memory
# DFF
Weight_memory = nx.Graph(position='chip',
                         array_size=[3, 3],
                         BW_output=[3, 3]
                         )
Weight_memory.add_node('DFF',
                       energy=0
                       )

# Define interface of weight between weight memory and PE
# current DAC, in-block element parallel, D -> I
Weight_interface = nx.Graph(position='chip',
                            BW_input=[3, 3],
                            batch_input=1,
                            BW_output=[3, 3]
                            )
Weight_interface.add_node('weighted current biasing',
                          cell_template='current DAC',
                          BW_input=[1, 1],
                          batch_input=1,
                          BW_output=[1, 1],
                          duplication=[1, 9],
                          intrinsic_delay=1,
                          domain_input='digit',
                          domain_output='current',
                          energy=dac_d_to_c(supply=0.8, load_capacitance=2e-12, t_readout=7.9e-6, resolution=3,
                                            num_current_path=1).energy()
                          # value_input=w,
                          # value_output=np.random.normal(w, w * w_mismatch),
                          # ideal_output=w
                          )

# Define PE
# current-domain MAC, column parallel, I -> V, max-pooling (part-1)
PE_array = nx.Graph(position='column',
                    BW_input=[[3, 3], [3, 126]],  # [w, x]
                    batch_input=1,
                    BW_output=[1, 42]
                    )
PE = nx.Graph(BW_input=[[3, 3], [3, 3]],  # [w, x]
              batch_input=1,
              BW_output=[1, 1],
              duplication=[1, 42],
              domain_input=['current', 'time'],
              domain_output='voltage'
              )
PE_array.add_node(PE)
PE.add_node('SCI',
            cell_template='current mirror',
            BW_input=[[1, 1], [1, 1]],
            batch_input=1,
            BW_output=[1, 1],
            duplication=[1, 9],
            intrinsic_delay=1,
            domain_input=['current', 'time'],
            domain_output='charge',
            energy=dac_d_to_c(supply=0.8, load_capacitance=2e-12, t_readout=7.9e-6, resolution=3,
                              num_current_path=1).energy()
            # value_input=[Weight_interface.nodes['weighted current biasing']['value_output'],
            #             Pixel_array.nodes['pixel']['value_output']],
            # value_output=Weight_interface.nodes['weighted current biasing']['value_output'] *
            #             Pixel_array.nodes['pixel']['value_output'],
            # ideal_output=Weight_interface.nodes['weighted current biasing']['value_output'] *
            #             Pixel_array.nodes['pixel']['value_output']
            )
PE.add_node('capacitor',
            cell_template='voltage sampler',
            BW_input=[1, 1],
            batch_input=9,
            BW_output=[1, 1],
            duplication=[1, 4],
            intrinsic_delay=1,
            domain_input='charge',
            domain_output='voltage',
            energy=AnalogMemory(type='passive', capacitance=2e-12, supply=0.8, droop_rate=0, t_sample=0, t_hold=0,
                                resolution=0, gain_opamp=0).energy()
            # value_input=PE.nodes['SCI']['value_output'],
            # value_output=PE.nodes['SCI']['value_output'] / np.random.normal(C, C * C_mismatch),
            # ideal_output=PE.nodes['SCI']['value_output'] / C
            )
PE.add_node('comparator',
            cell_template='comparator',
            duplication=[1, 1],
            domain_input='voltage',
            domain_output='digit',
            energy=Comparator(supply=0.8, i_bias=10e-6, t_readout=10e-9).energy()
            )

PE.add_edge('SCI', 'capacitor',
            transmission_cycle=1)
PE.add_edge('capacitor', 'comparator',
            transmission_cycle=1)
PE.graph['computation_cycle'] = \
    (
            PE.nodes['SCI']['intrinsic_delay']
            + PE.edges['SCI', 'capacitor']['transmission_cycle']
            + PE.nodes['capacitor']['intrinsic_delay']
    ) \
    * PE.nodes['SCI']['duplication'] + \
    PE.edges['capacitor', 'comparator']['transmission_cycle'] * PE.nodes['comparator'][
        'duplication']

# Define ADC
# SS ADC, column parallel, V -> D
ADC_array = nx.Graph(position='column',
                     BW_input=[1, 21],
                     batch_input=1,
                     BW_output=[1, 21]
                     )
ADC_array.add_node('ADC',
                   duplication=[1, 21],
                   intrinsic_delay=8,
                   domain_input='voltage',
                   domain_output='digit',
                   resolution=3,
                   energy=ADC(type='SS', FOM=100e-15, resolution=3, sampling_rate=4e5).energy()
                   )

# Define digital processor
# max-pooling (part-2) + FC
Digital_processor = nx.Graph(BW_input=[1, 21, ADC_array.nodes['ADC']['resolution']],
                             BW_output=[1, 21, ADC_array.nodes['ADC']['resolution']]
                             )
Digital_processor.add_node('max pooling')
Digital_processor.add_node('fc')

# derive mismatch from end-accuracy
# analytical_output = I * delta_t / C, I: weight, delta_t: x
# x_mismatch = 0
# ideal_output = PE.nodes['capacitor']['ideal_output']
# actual_output = PE.nodes['capacitor']['value_output']
# [[x, x_mismatch], [w, w_mismatch], [C, C_mismatch]] = A_Kind_of_Optimizer(ideal_output, actual_output)

# determine unit performance
# performance is returned in [energy, latency, area]
# Pixel_array.nodes['pixel']['performance'] = hw.PWM.performance(pitch=7.6, technology=0.18, x_mismatch)
# Weight_memory.nodes['DFF']['performance'] = hw.DFF.performance()
# Weight_interface.nodes['weighted current biasing']['performance'] = hw.Current_DAC.performance(reso=3, w_mismatch)
# PE.nodes['SCI']['performance'] = hw.Current_Mirror.performance()
# PE.nodes['capacitor']['performance'] = hw.Voltage_Sampler.performance(C, C_mismatch)
# PE.nodes['comparator']['performance'] = hw.Comparator.performance()

# mapping checkpoint, loop over back, determine how to get system performance from unit performance

# sensor IO is kind of standard and universal, so it is excluded from the hardware graph
# Define sensor system
Sensor_System = nx.Graph()
Sensor_System.add_node(Pixel_array)
Sensor_System.add_node(Weight_interface)
Sensor_System.add_node(PE_array)
Sensor_System.add_node(ADC)
Sensor_System.add_node(Digital_processor)

Sensor_System.add_edge(Pixel_array, PE_array,
                       transmission_cycle=1)
Sensor_System.add_edge(Weight_interface, PE_array,
                       transmission_cycle=1)
Sensor_System.add_edge(PE_array, ADC,
                       transmission_cycle=1)
Sensor_System.add_edge(ADC, Digital_processor,
                       transmission_cycle=1)

print()

# todo: add domain checker
# todo: derive number of usage from BW connection
# todo: add get_min and get_max
# todo: add power and delay model
# todo: add activity factor and technology-scaling factor

