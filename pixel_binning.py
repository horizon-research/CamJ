import numpy as np
import networkx as nx
from acomp_library import *
# import SW_pipeline as sw
import matplotlib.pyplot as plt

H = 256  # horizontal dimension of pixel array
V = 256  # vertical dimension of pixel array
tech = 180  # [nm]
pitch = 5  # [um]

# define pixel array (used for exposure)
Pixel_array = nx.Graph(color_filter='none',
                       BW_input=[1, H],
                       BW_output=[1, H]  # rolling shutter, one vertical readout bus
                       )
Pixel_array.add_node('pixel',
                     BW_input=[1, 1],
                     batch_input=1,
                     BW_output=[1, 1],
                     duplication=[126, 126],  # [n_row, n_col]
                     domain_input='optical',
                     domain_output='voltage',
                     energy=APS(pd_capacitance=100e-15,  # [F]
                                pd_supply=2.5,  # [V]
                                num_transistor=4,
                                fd_capacitance=10e-15,  # [F]
                                num_readout=2,
                                t_readout=1e-6,  # [s]
                                load_capacitance=1e-12 + get_pixel_parasitic(array_v=V, technology=tech, pitch=pitch)
                                # [F]
                                ).energy()
                     )

# define PE array for pixel binning
PE_array = nx.Graph(position='pixel',
                    BW_input=[2, H],
                    batch_input=1,
                    BW_output=[1, H / 2]  # readout once at every two rows
                    )
PE_array.add_node('capacitor',
                  BW_input=[2, 2],
                  batch_input=1,
                  BW_output=[1, 1],
                  duplication=[1, H / 2],
                  intrinsic_delay=1,
                  domain_input='voltage',
                  domain_output='voltage',
                  energy=AnalogMemory(type='passive',
                                      capacitance=10e-15,  # [F]
                                      supply=2.5  # [V]
                                      ).energy()
                  )
