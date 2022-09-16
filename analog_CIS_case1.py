# Case study of "A 0.5-V Real-Time Computational CMOS Image Sensor With Programmable Kernel for Feature Extraction", in JSSC'21.
# https://ieeexplore.ieee.org/document/9250500


# black-box-level attribute definition
# BW_input: # of input wires
# BW_output: # of output wires
# batch_input: # of inputs in the unit of BW_input required by one batch of outputs
# computation_cycle: # of clock cycles required by one batch of outputs

# circuit-level attribute definition
# duplication: # of identical cells in the unit


# if BW_input (n^th stage) = BW_output ((n-1)^th stage), then no intermediate buffer is needed.
# Designers should select circuit template and provide timing diagram

import numpy as np
import networkx as nx
import hw_config_analog as config
import matplotlib.pyplot as plt

# Define pixel
# pixel exposure (light -> PWM), three-row-wise
Pixel_array = nx.Graph(array_size=[128, 128],  # [n_row, n_col]
                       color_filter='none',
                       BW_output=[3, 128]  # output through 3 column bus
                       )
Pixel_array.add_node('pixel',
                     performance=config.PWM.performance(pitch=7.6, technology=0.18)
                     )

# Define weight memory
# DFF
Weight_memory = nx.Graph(array_size=[1, 9],
                         BW_output=[1, 9]
                         )
Weight_memory.add_node('DFF',
                       performance=config.DFF.performance(wordwidth=5)
                       )

# Define interface of weight between weight memory and PE
# current DAC, in-block element parallel, D -> I
Weight_interface = nx.Graph(array_size=[1, 9],
                            BW_input=[1, 9],
                            batch_input=1,
                            BW_output=[1, 9],
                            computation_cycle=1
                            )
Weight_interface.add_node('weighted current biasing',
                          cell_template='current DAC',
                          performance=config.Current_DAC.performance(resolution=3)
                          )

# Define PE
# current-domain MAC, column parallel, I -> V
PE = nx.Graph(array_size=[1, 128],
              BW_input=[[1, 9], [3, 128]],  # [w, x]
              batch_input=3,
              BW_output=[1, 128],
              computation_cycle=3
              )
PE.add_node('SCI',
            cell_template='current mirror',
            performance=config.Current_Mirror.performance(VDD=0.5, I=1e-6, t=5e-6),
            duplication=6
            )
PE.add_node('capacitor',
            cell_template='voltage sampler',
            performance=config.Voltage_Sampler.performance(capacitance=),
            duplication=2
            )

PE.add_edge('SCI', 'capacitor',
            transmission_cycle=1)

# Define ADC
# SS ADC, column parallel, V -> D
ADC = nx.Graph(array_size=[1, 128],
               BW_input=[1, 128],
               batch_input=1,
               BW_output=[1, 128],
               computation_cycle=8)
ADC.add_node('ADC',
             data=config.ADC(type='SS', FOM=20e-15, resolution=8, sampling_rate=4e5))

# Define Sensor IO
# MUX + shift register
Sensor_IO = nx.Graph(BW_input=[1, 128, ADC.nodes['ADC']['resolution']],
                     BW_output=[1, 128, ADC.nodes['ADC']['resolution']]
                     )
Sensor_IO.add_node('mux and shift register',
                   performance=
                   )

# Define sensor system
Sensor_System = nx.Graph()
Sensor_System.add_node(Pixel_array)
Sensor_System.add_node(Weight_interface)
Sensor_System.add_node(PE)
Sensor_System.add_node(ADC)
Sensor_System.add_node(Sensor_IO)

Sensor_System.add_edge(Pixel_array, PE,
                       transmission_cycle=1)
Sensor_System.add_edge(Weight_interface, PE,
                       transmission_cycle=1)
Sensor_System.add_edge(PE, ADC,
                       transmission_cycle=1)
Sensor_System.add_edge(ADC, Sensor_IO,
                       transmission_cycle=1)

# looking for analog microarchitecture modelling? (benchmark)
# is it reasonable to sum up power/area? (maybe a regression model)
# how to deal with inter/intra-PE pipeline
# how to define inter-stage buffer?
