# CamJ: In-sensor Processing Simulator

CamJ is an in-sensor processing simulator. CamJ framwork helps sensor designer to easily describe
their sensor designs using high-level API and evaluates the energy and accuracy of their designs.

## What's Inside

CamJ has two main functionalities, power/energy estimation and functional simulation (noise modeling).
We put the core functions of these two parts into two directories:

- sim_core: contains the power simulation API and core implementations.
- functional_core: contains noising modeling API and core implementations.

For more details about these two parts, Go and check these two subdirectories.

## Design Philosophy

To use our framework, users need to specify the sensor configuration using CamJ API. CamJ API provides
three major parts to allow users freely describe their designs. These three parts are:

- software pipeline configuration: this file describes how computation are done in software. Most image pipeline can be described as a graph, we design CamJ API so that each node is a processing stage
and the connection is the data dependency. In each node, we constrain the computations to be stencil
operations, which is most commonly used operation in image/graph processing.
- hardware desription: this file desribes the hardware configuration. It is like how you decribe
hardware in other HDLs, but it is much simpler. CamJ also provides some built-in hardware modules 
so that you can direcly plog in your design.
- software-to-hardware mapping function: this part describes how to map software computation stages
to hardware components.