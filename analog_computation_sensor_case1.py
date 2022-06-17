# JSSC'21

import numpy as np
import networkx as nx
import hw_config_tianrui as config

# pixel exposure (light -> PWM), three-row-wise
Pixel = nx.Graph(array_size=[128, 128])
Pixel.add_node('pixel',
               data=config.Pixel(pitch=7.6, ismonochrome=False, type='PWM'),
               exposure=config.Pixel.exposure(type='multi_rolling_shutter', n_rows=3))

# weight storage, DFF
DigitalStorage = config.DigitalStorage(size=[1, 9], )
config.DFF(DigitalStorage)

# interface of weight (D -> I), DAC-2
Interface_weight = config.AnalogCell(type=['DAC', 2])
Interface_weight_array = Interface_weight.form_array(size=[1, 9])

# MAC, column parallel (I -> V)
PE = nx.Graph(array_size=[1, 128])  # each cell is a node
PE.add_node('SCI-1',
            data=config.AnalogCell(celltype='amplifier-2'))
PE.add_node('SCI-2',
            data=config.AnalogCell(celltype='amplifier-2'))
PE.add_node('SCI-3',
            data=config.AnalogCell(celltype='amplifier-2'))
PE.add_node('SCI-4',
            data=config.AnalogCell(celltype='amplifier-2'))
PE.add_node('SCI-5',
            data=config.AnalogCell(celltype='amplifier-2'))
PE.add_node('SCI-6',
            data=config.AnalogCell(celltype='amplifier-2'))

PE.add_node('C_P',
            data=config.AnalogCell(celltype='sampler-1'))
PE.add_node('C_N',
            data=config.AnalogCell(celltype='sampler-1'))

PE.add_node('comparator',
            data=config.AnalogCell(celltype='comparator-1'))

PE.add_edges_from([('SCI-1', 'C_P'), ('SCI-2', 'C_P'), ('SCI-3', 'C_P')])
PE.add_edges_from([('SCI-4', 'C_N'), ('SCI-5', 'C_N'), ('SCI-6', 'C_N')])
PE.add_edges_from([('C_P', 'comparator'), ('C_N', 'comparator')])

# ADC (V -> D), SS ADC
ADC = nx.Graph(array_size=[1, 128])
ADC.add_node('ADC',
             data=config.ADC(type='SS', resolution=8))

# define system
Sensor_System = nx.Graph()
Sensor_System.add_node(Pixel)
Sensor_System.add_node(PE)
Sensor_System.add_node(ADC)
