# Case study of "Design of an Always-On Image Sensor Using anAnalog Lightweight Convolutional Neural Network", in Sensors'20.
# https://www.mdpi.com/1424-8220/20/11/3101


import numpy as np
import networkx as nx
import hw_config_analog as config
import matplotlib.pyplot as plt

# Define pixel
# pixel exposure (light -> voltage), rolling shutter
Pixel_array = nx.Graph(array_size=[120, 160],  # [n_row, n_col]
                       color_filter='none',
                       BW_input=[1, 160],  # rolling shutter
                       BW_output=[1, 160]
                       )  # black-box level
Pixel_array.add_node('pixel',
                     performance=config.APS.performance(pitch=, technology=0.11, type='4T')
                     )  # circuit level

# Define convolution unit
# switch-cap
Convolution_unit_1 = nx.Graph(array_size=[1, 80],
                              BW_input=[2, 80],  # each unit has two input wires
                              batch_input=2,  # two batches of input are needed
                              BW_output=[1, 80],  # each unit has one output wire
                              computation_cycle=1
                              )
Convolution_unit_1.add_node('Convolution_unit_1',
                            cell_template='passive switch cap',
                            performance=config.Passive_SC.performance(unit_cap=0.5e-12)
                            )
Convolution_unit_2 = nx.Graph(array_size=[1, 20],
                              BW_input=[2, 20],
                              batch_input=2,
                              BW_ouptut=[1, 20],
                              computation_cycle=1
                              )
Convolution_unit_2.add_node('Convolution_unit_2',
                            cell_template='passive switch cap',
                            performance=config.Passive_SC.performance(unit_cap=0.5e-12)
                            )

# Define max-pooling unit
# voltage max circuit
MaxPooling_unit_1 = nx.Graph(array_size=[1, 40],
                             BW_input=[2, 40],
                             batch_input=2,
                             BW_output=[1, 40],
                             computation_cycle=1
                             )
MaxPooling_unit_1.add_node('MaxPooling_unit_1',
                           cell_template='voltage WTA',
                           performance=config.Voltage_WTA.performance(bias_current=)
                           )
MaxPooling_unit_2 = nx.Graph(array_size=[1, 10],
                             BW_input=[2, 10],
                             batch_input=2,
                             BW_output=[1, 10],
                             computation_cycle=1
                             )
MaxPooling_unit_2.add_node('MaxPooling_unit_2',
                           cell_template='voltage WTA',
                           performance=config.Voltage_WTA.performance(bias_current=)
                           )

# Define ADC
# SS ADC, column parallel, V -> D
ADC = nx.Graph(array_size=[1, 10],
               BW_input=[1, 10],
               batch_input=1,
               BW_output=[1, 10],
               computation_cycle=4
               )
ADC.add_node('ADC',
             performance=config.ADC(type='SS', FOM=20e-15, resolution=4, sampling_rate=4e5))

# Define Sensor IO
# MUX + shift register
Sensor_IO = nx.Graph(BW_input=[1, 10, ADC.nodes['ADC']['resolution']],
                     BW_output=[1, 10, ADC.nodes['ADC']['resolution']]
                     )
Sensor_IO.add_node('mux and shift register and mipi csi transceiver',
                   performance=
                   )

# Define sensor system
Sensor_System = nx.Graph()
Sensor_System.add_node(Pixel_array)
Sensor_System.add_node(Convolution_unit_1)
Sensor_System.add_node(Convolution_unit_2)
Sensor_System.add_node(MaxPooling_unit_1)
Sensor_System.add_node(MaxPooling_unit_2)
Sensor_System.add_node(ADC)
Sensor_System.add_node(Sensor_IO)

Sensor_System.add_edge(Pixel_array, Convolution_unit_1,
                       transmission_cycle=1)
Sensor_System.add_edge(Convolution_unit_1, MaxPooling_unit_1,
                       transmission_cycle=1)
Sensor_System.add_edge(MaxPooling_unit_1, Convolution_unit_2,
                       transmission_cycle=1)
Sensor_System.add_edge(Convolution_unit_2, MaxPooling_unit_2,
                       transmission_cycle=1)
Sensor_System.add_edge(MaxPooling_unit_2, ADC,
                       transmission_cycle=1)
Sensor_System.add_edge(ADC, Sensor_IO,
                       transmission_cycle=1)

total_delay = Sensor_System.edges[Pixel_array, Convolution_unit_1]['transmission_cycle'] \
              * Convolution_unit_1['batch_input'] + Convolution_unit_1['computation_cycle'] + \
              Sensor_System.edges[Convolution_unit_1, MaxPooling_unit_1]['transmission_cycle'] \
              * MaxPooling_unit_1['batch_input'] + MaxPooling_unit_1['computation_cycle'] + \
              Sensor_System.edges[MaxPooling_unit_1, Convolution_unit_2]['transmission_cycle'] \
              * Convolution_unit_2['batch_input'] + Convolution_unit_2['computation_cycle'] + \
              Sensor_System.edges[Convolution_unit_2, MaxPooling_unit_2]['transmission_cycle'] \
              * MaxPooling_unit_2['batch_input'] + MaxPooling_unit_2['computation_cycle'] + \
              Sensor_System.edges[MaxPooling_unit_2, ADC]['transmission_cycle'] \
              * ADC['batch_input'] + ADC['computation_cycle'] + \
              Sensor_System.edges[ADC, Sensor_IO]['transmission_cycle']
