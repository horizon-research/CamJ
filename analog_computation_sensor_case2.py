# Case study of "A 0.8V Intelligent Vision Sensor with Tiny Convolutional Neural Network and Programmable Weights Using Mixed-Mode Processing-in-Sensor Technique for Image Classification", in ISSCC'22.
# https://ieeexplore.ieee.org/document/9731675
# 1. Define each component in the manner of column circuitry connection
# 2. The entire system is the duplication of column circuitry


import numpy as np
import networkx as nx
import hw_config_tianrui as config
import matplotlib.pyplot as plt

# Define pixel
# pixel exposure (light -> PWM), three-row-wise
Pixel_array = nx.Graph(array_size=[128, 128],  # [n_row, n_col]
                       color_filter='none',
                       # inputBW=3,  # select 3 pixel rows at once
                       outputBW=[3, 128],  # output through 3 column bus
                       fire_factor=3)
Pixel_array.add_node('pixel',
                     data=config.Pixel(pitch=7.6, technology=0.18, type='PWM'))

# Define weight memory
# DFF
Weight_memory = nx.Graph(array_size=[1, 9],
                         outputBW=[1, 3],
                         fire_factor=3)
Weight_memory.add_node('DFF', data=config.DFF())

# Define interface of weight between weight memory and PE
# current DAC, in-block element parallel, D -> I
Interface_weight = nx.Graph(array_size=[1, 9],
                            # column_share_factor=128,
                            # inputBW=3,
                            outputBW=[1, 3],
                            fire_factor=3)
Interface_weight.add_node('weighted current biasing',
                          data=config.AnalogCell(celltype='DAC-2'))

# Define PE
# current-domain MAC, column parallel, I -> V
# each cell template is a node
PE = nx.Graph(array_size=[1, 128],
              # column_share_factor=1,
              inputBW=[[3, 1], [3, 1]],  # [x, w]
              outputBW=1)
PE.add_node('SCI-1',
            data=config.AnalogCell(celltype='current mirror'),
            fire_factor=3)
PE.add_node('SCI-2',
            data=config.AnalogCell(celltype='current mirror'),
            fire_factor=3)
PE.add_node('SCI-3',
            data=config.AnalogCell(celltype='current mirror'),
            fire_factor=3)
PE.add_node('SCI-4',
            data=config.AnalogCell(celltype='current mirror'),
            fire_factor=3)
PE.add_node('SCI-5',
            data=config.AnalogCell(celltype='current mirror'),
            fire_factor=3)
PE.add_node('SCI-6',
            data=config.AnalogCell(celltype='current mirror'),
            fire_factor=3)
PE.add_node('C_P',
            data=config.AnalogCell(celltype='voltage sampler'))
PE.add_node('C_N',
            data=config.AnalogCell(celltype='voltage sampler'))

PE.add_edges_from([('SCI-1', 'C_P'), ('SCI-2', 'C_P'), ('SCI-3', 'C_P')],
                  transmission_cycle=1)
PE.add_edges_from([('SCI-4', 'C_N'), ('SCI-5', 'C_N'), ('SCI-6', 'C_N')],
                  transmission_cycle=1)

# Define ADC
# SS ADC, column parallel, V -> D
ADC = nx.Graph(array_size=[1, 128],
               # column_share_factor=1,
               inputBW=1,
               fire_factor=1)
ADC.add_node('ADC',
             data=config.ADC(type='SS', FOM=20e-15, resolution=8, sampling_rate=4e5))

# Define Sensor IO
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
Sensor_System.add_node(Interface_weight)
Sensor_System.add_node(PE)
Sensor_System.add_node(ADC)

Sensor_System.add_edge(Pixel_array, PE)
Sensor_System.add_edge(Interface_weight, PE)
Sensor_System.add_edge(PE, ADC)

# looking for analog microarchitecture modelling? (benchmark)
# is it reasonable to sum up power/area? (maybe a regression model)
# how to deal with inter/intra-PE pipeline
# how to define inter-stage buffer?
