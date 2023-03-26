# TCAS-I 22 Senputing

This example describes the sensor design from the TCAS-I 2022 paper: [Senputing: An Ultra-Low-Power Always-On Vision Perception Chip Featuring the Deep Fusion of Sensing and Computing](https://ieeexplore.ieee.org/document/9464962)

In this example, we simulate a BNN network. The first FC layer is operated in analog domain and the 
second layer is operated in digital domain.

<img width="1043" alt="tcas_i22_flowchat" src="https://user-images.githubusercontent.com/21286132/221265134-743a15ee-3acd-4257-a7b0-df506278de74.png">

The figure in the original paper explains the sensor design quite well. For each pixel, the SRAM Macro
will control the switches `S2` and `S3` so that all pixels with weight `+1` are accumulated as the sumed 
voltage. The same as the pixels with weight `-1`. Then, the sumed votage with weight `+1` and the sumed  voltage with weight `-1` will go to comparator to compare. The comparator serves as `ReLU`. If voltage `+1`
is greater than voltage `-1`, then the comparator will output `+1`. Otherwise, the comparator will output 0.
