# Case study of "A 0.8V Intelligent Vision Sensor with Tiny Convolutional Neural Network and Programmable Weights Using Mixed-Mode Processing-in-Sensor Technique for Image Classification", in ISSCC'22.
# https://ieeexplore.ieee.org/document/9731675


import numpy as np
import networkx as nx
import hw_config_tianrui as config
import matplotlib.pyplot as plt

# Define pixel
# pixel exposure (light -> PWM), three-row-wise
Pixel_array = nx.Graph(array_size=[128, 128],  # [n_row, n_col]
                       color_filter='none',
                       outputBW=[3, 128]  # output through 3 column bus
                       )
Pixel_array.add_node('pixel',
                     performance=config.PWM.performance(pitch=7.6, technology=0.18))

# Define weight memory
# DFF
Weight_memory = nx.Graph(array_size=[1, 9],
                         outputBW=[1, 9]
                         )
Weight_memory.add_node('DFF',
                       performance=config.DFF.performance())

# Define interface of weight between weight memory and PE
# current DAC, in-block element parallel, D -> I
Weight_interface = nx.Graph(array_size=[1, 9],
                            outputBW=[1, 9]
                            )
Weight_interface.add_node('weighted current biasing',
                          cell_template='current DAC',
                          performance=config.Current_DAC.performance(resolution=3)
                          )

# Define PE
# current-domain MAC, column parallel, I -> V
# each cell template is a node
PE = nx.Graph(array_size=[1, 42],
              # column_share_factor=1,
              inputBW=[[3, 3], [3, 3]],  # [x, w]
              outputBW=1,
              output_spatial_factor=,
              output_temporal_factor=)
PE.add_node('SCI',
            cell_template='current mirror',
            performance=config.Current_Mirror.performance(),
            duplication=9)
PE.add_node('capacitor',
            performance=config.Voltage_Sampler.performance(),
            duplication=4)
PE.add_node('comparator',
            performance=config.Comparator.performance())

PE.add_edges_from([('SCI', 'capacitor'), ('capacitor', 'comparator')],
                  transmission_cycle=1)

# Define ADC
# SS ADC, column parallel, V -> D
ADC = nx.Graph(array_size=[1, 21],
               inputBW=1,
               outputBW=1)
ADC.add_node('ADC',
             data=config.ADC(type='SS', FOM=20e-15, resolution=8, sampling_rate=4e5))

# Define digital processor
# max-pooling (part-2) + FC
Digital_processor = nx.Graph(inputBW=1,
                             outputBW=1)
Digital_processor.add_node('max pooling')
Digital_processor.add_node('fc')

# Define sensor IO
# MUX + shift register
Sensor_IO = nx.Graph(inputBW=1,
                     fire_factor=1)
Sensor_IO.add_node('MUX',
                   data=)
Sensor_IO.add_node('shift_register',
                   data=)
Sensor_IO.add_edges_from([('MUX', 'shift_register')],
                         transmission_cycle=1)

# Define sensor system
Sensor_System = nx.Graph()
Sensor_System.add_node(Pixel_array)
Sensor_System.add_node(Weight_interface)
Sensor_System.add_node(PE)
Sensor_System.add_node(ADC)

Sensor_System.add_edges_from([(Pixel_array, PE)],
                             transmission_cycle=1)
Sensor_System.add_edge(Weight_interface, PE)
Sensor_System.add_edge(PE, ADC)
