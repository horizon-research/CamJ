# Case study of "A 0.5-V Real-Time Computational CMOS Image Sensor With Programmable Kernel for Feature Extraction", in JSSC'21.
# https://ieeexplore.ieee.org/document/9250500


# attribute definition
# inputBW: input data volume in its datatype per hardware unit fire
# outputBW: output data volume in its datatype per hardware unit fire

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
                     performance=config.PWM.performance(pitch=7.6, technology=0.18, type='PWM'))

# Define weight memory
# DFF
Weight_memory = nx.Graph(array_size=[1, 9],
                         outputBW=[1, 9]
                         )
Weight_memory.add_node('DFF',
                       performance=config.DFF.performance(wordwidth=5))

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
PE = nx.Graph(array_size=[1, 128],
              # column_share_factor=1,
              inputBW=[[3, 1], [1, 3]],  # [x, w]
              outputBW=1,
              output_spatial_factor=,
              output_temporal_factor=)
PE.add_node('SCI-1',
            cell_template='current mirror',
            performance=config.Current_Mirror.performance(VDD=0.5, I=1e-6, t=5e-6),
            fire_factor=3)
PE.add_node('SCI-2',
            cell_template='current mirror',
            performance=config.Current_Mirror.performance(VDD=0.5, I=1e-6, t=5e-6),
            fire_factor=3)
PE.add_node('SCI-3',
            cell_template='current mirror',
            performance=config.Current_Mirror.performance(VDD=0.5, I=1e-6, t=5e-6),
            fire_factor=3)
PE.add_node('SCI-4',
            cell_template='current mirror',
            performance=config.Current_Mirror.performance(VDD=0.5, I=1e-6, t=5e-6),
            fire_factor=3)
PE.add_node('SCI-5',
            cell_template='current mirror',
            performance=config.Current_Mirror.performance(VDD=0.5, I=1e-6, t=5e-6),
            fire_factor=3)
PE.add_node('SCI-6',
            cell_template='current mirror',
            performance=config.Current_Mirror.performance(VDD=0.5, I=1e-6, t=5e-6),
            fire_factor=3)
PE.add_node('C_P',
            performance=config.Voltage_Sampler.performance())
PE.add_node('C_N',
            performance=config.Voltage_Sampler.performance())

PE.add_edges_from([('SCI-1', 'C_P'), ('SCI-2', 'C_P'), ('SCI-3', 'C_P')],
                  transmission_cycle=1)
PE.add_edges_from([('SCI-4', 'C_N'), ('SCI-5', 'C_N'), ('SCI-6', 'C_N')],
                  transmission_cycle=1)

# Define ADC
# SS ADC, column parallel, V -> D
ADC = nx.Graph(array_size=[1, 128],
               inputBW=1,
               outputBW=1)
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
Sensor_System.add_node(Weight_interface)
Sensor_System.add_node(PE)
Sensor_System.add_node(ADC)

Sensor_System.add_edges_from([(Pixel_array, PE)],
                             transmission_cycle=1)
Sensor_System.add_edge(Weight_interface, PE)
Sensor_System.add_edge(PE, ADC)

# looking for analog microarchitecture modelling? (benchmark)
# is it reasonable to sum up power/area? (maybe a regression model)
# how to deal with inter/intra-PE pipeline
# how to define inter-stage buffer?
