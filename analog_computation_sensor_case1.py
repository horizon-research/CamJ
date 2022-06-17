# Case study of "A 0.5-V Real-Time Computational CMOS Image Sensor With Programmable Kernel for Feature Extraction", in JSSC'21.
# https://ieeexplore.ieee.org/document/9250500
# 1. Define each component in the manner of column circuitry connection
# 2. The entire system is the duplication of column circuitry


import numpy as np
import networkx as nx
import hw_config_tianrui as config
import matplotlib.pyplot as plt

# Define pixel
# pixel exposure (light -> PWM), three-row-wise
Pixel = nx.Graph(array_size=[128, 1],
                 column_share_factor=1)
Pixel.add_node('pixel',
               data=config.Pixel(pitch=7.6, ismonochrome=False, type='PWM'),
               inputBW=3,
               outputBW=3)

# Define weight memory
# DFF
DigitalStorage = config.DigitalStorage(size=[1, 9], )
config.DFF()

# Define interface of weight between weight memory and PE
# current DAC, in-block element parallel, D -> I
Interface_weight = nx.Graph(array_size=[1, 9],
                            column_share_factor=128)
Interface_weight.add_node('weighted current biasing',
                          data=config.AnalogCell(celltype='DAC-2'),
                          inputBW=9,
                          outputBW=9)

# Define PE
# current-domain MAC, column parallel, I -> V
PE = nx.Graph(array_size=[1, 1],
              column_share_factor=1)  # each cell template is a node
PE.add_node('SCI-1',
            data=config.AnalogCell(celltype='amplifier-2'),
            inputBW=1,
            outputBW=1)
PE.add_node('SCI-2',
            data=config.AnalogCell(celltype='amplifier-2'),
            inputBW=1,
            outputBW=1)
PE.add_node('SCI-3',
            data=config.AnalogCell(celltype='amplifier-2'),
            inputBW=1,
            outputBW=1)
PE.add_node('SCI-4',
            data=config.AnalogCell(celltype='amplifier-2'),
            inputBW=1,
            outputBW=1)
PE.add_node('SCI-5',
            data=config.AnalogCell(celltype='amplifier-2'),
            inputBW=1,
            outputBW=1)
PE.add_node('SCI-6',
            data=config.AnalogCell(celltype='amplifier-2'),
            inputBW=1,
            outputBW=1)
PE.add_node('C_P',
            data=config.AnalogCell(celltype='sampler-1'),
            inputBW=3,
            outputBW=1)
PE.add_node('C_N',
            data=config.AnalogCell(celltype='sampler-1'),
            inputBW=3,
            outputBW=1)
PE.add_node('comparator',
            data=config.AnalogCell(celltype='comparator-1'),
            inputBW=2,
            outputBW=1)

PE.add_edges_from([('SCI-1', 'C_P'), ('SCI-2', 'C_P'), ('SCI-3', 'C_P')], aBW=1)
PE.add_edges_from([('SCI-4', 'C_N'), ('SCI-5', 'C_N'), ('SCI-6', 'C_N')], aBW=1)
PE.add_edges_from([('C_P', 'comparator'), ('C_N', 'comparator')], aBW=1)

# Define ADC
# SS ADC, column parallel, V -> D
ADC = nx.Graph(array_size=[1, 1],
               column_share_factor=1)
ADC.add_node('ADC',
             data=config.ADC(type='SS', resolution=8))

# Define sensor system
Sensor_System = nx.Graph()
Sensor_System.add_node(Interface_weight)
Sensor_System.add_node(Pixel)
Sensor_System.add_node(PE)
Sensor_System.add_node(ADC)

Sensor_System.add_edge(Pixel, PE, aBW=3)
Sensor_System.add_edge(Interface_weight, PE, aBW=1)
Sensor_System.add_edge(PE, ADC, aBW=1)
