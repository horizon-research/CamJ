# Case study of "Design of an Always-On Image Sensor Using anAnalog Lightweight Convolutional Neural Network", in Sensors'20.
# https://www.mdpi.com/1424-8220/20/11/3101


import numpy as np
import networkx as nx
import hw_config_tianrui as config
import matplotlib.pyplot as plt

# Define pixel
# pixel exposure (light -> PWM), three-row-wise
Pixel_array = nx.Graph(array_size=[120, 160],  # [n_row, n_col]
                       color_filter='none',
                       outputBW=[1, 160]  # output through 3 column bus
                       )
Pixel_array.add_node('pixel',
                     performance=config.PWM.performance(pitch=, technology=0.11, type='APS'))

# Define convolution unit
# switch-cap
Convolution_unit_1 = nx.Graph(array_size=[1, 160],
                              inputBW=,
                              outputBW=[1, 160]
                              )
Convolution_unit_1.add_node('Convolution_unit_1',
                            cell_template='passive switch cap',
                            performance=config.Passive_SC.performance())
Convolution_unit_2 = nx.Graph(array_size=[1, 20],
                              inputBW=,
                              outputBW=[1, 20]
                              )
Convolution_unit_2.add_node('Convolution_unit_2',
                            cell_template='passive switch cap',
                            performance=config.Passive_SC.performance())

# Define max-pooling unit
# voltage max circuit
MaxPooling_unit_1 = nx.Graph(array_size=[1, 40],
                             inputBW=,
                             outputBW=[1, 40]
                             )
MaxPooling_unit_1.add_node('MaxPooling_unit_1',
                           cell_template='voltage WTA',
                           performance=config.Voltage_WTA.performance())
MaxPooling_unit_2 = nx.Graph(array_size=[1, 10],
                             inputBW=,
                             outputBW=[1, 10]
                             )
MaxPooling_unit_2.add_node('MaxPooling_unit_2',
                           cell_template='voltage WTA',
                           performance=config.Voltage_WTA.performance())

# Define ADC
# SS ADC, column parallel, V -> D
ADC = nx.Graph(array_size=[1, 10],
               inputBW=[1, 10],
               outputBW=[1, 10])
ADC.add_node('ADC',
             data=config.ADC(type='SS', FOM=20e-15, resolution=4, sampling_rate=4e5))

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
Sensor_System.add_node(Convolution_unit_1)
Sensor_System.add_node(Convolution_unit_2)
Sensor_System.add_node(MaxPooling_unit_1)
Sensor_System.add_node(MaxPooling_unit_2)
Sensor_System.add_node(ADC)
Sensor_System.add_node(Sensor_IO)

Sensor_System.add_edges_from([(Pixel_array, Convolution_unit_1)],
                             transmission_cycle=1)
Sensor_System.add_edges_from([(Convolution_unit_1, MaxPooling_unit_1)],
                             transmission_cycle=1)
Sensor_System.add_edges_from([(MaxPooling_unit_1, Convolution_unit_2)],
                             transmission_cycle=1)
Sensor_System.add_edges_from([(Convolution_unit_2, MaxPooling_unit_2)],
                             transmission_cycle=1)
Sensor_System.add_edges_from([(MaxPooling_unit_2, ADC)],
                             transmission_cycle=1)
Sensor_System.add_edges_from([(ADC, Sensor_IO)],
                             transmission_cycle=1)
