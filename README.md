# CamJ: In-sensor Processing Simulator

CamJ is an in-sensor processing simulator. CamJ framwork helps sensor designer to easily describe
their sensor designs using high-level API and evaluates the energy and accuracy of their designs.

## What's Inside

CamJ has two main functionalities, power/energy estimation and functional simulation (noise modeling).
We put the core functions of these two parts into two directories:

- [sim_core](https://github.com/horizon-research/in-sensor-simulator/tree/main/sim_core): contains the power simulation API and core implementations.
- [functional_core](https://github.com/horizon-research/in-sensor-simulator/tree/main/functional_core): contains noising modeling API and core implementations.

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

Here shows the overview of our system. For more details, please refer our paper.

![camj](https://user-images.githubusercontent.com/21286132/216838473-c1477396-f1f6-4b04-a14b-7292c32948ad.png)

## How to Use

Folder `ieee_vr22` contains an example about how to describe a sensor design and a software pipeline
using CamJ API. In `ieee_vr22` folder, `sw_pipeline.py` describes the software dataflow, `hw_config`
describes hardware configuration and `mapping_file.py` describes the mapping mechanism between
software stages and hardware units. `functional_pipeline.py` is an additional file to describe
funtional simulation about noise modeling inside the sensor. No need to describe this file if you
don't want to do functional simulation. Inside `sw_pipeline.py`, CamJ provides an option to define
which software stage performs functional simulation.

In `example_run.py`, it contains how to use CamJ API to run simulation. First, we includes software/hardware configuration files which are defines using CamJ API.

```
from ieee_vr22.mapping_file import mapping_function
from ieee_vr22.sw_pipeline import sw_pipeline
from ieee_vr22.hw_config import hw_config
```

Next, get the major data structures for sensor simulation, as `main()` function shows.
```
	hw_dict = hw_config()
	mapping_dict = mapping_function()
	sw_stage_list = sw_pipeline()
```

To understand how to configure hardware and software pipeline please refer [sim_core](https://github.com/horizon-research/in-sensor-simulator/tree/main/sim_core) directory. If you want to understand more about noise modeling in CamJ, please refer to [functional_core](https://github.com/horizon-research/in-sensor-simulator/tree/main/functional_core).

Then, based on what we want to simulate, this example shows three different simulations. Call:
```
	launch_simulation(
		hw_dict = hw_dict,
		mapping_dict = mapping_dict,
		sw_stage_list = sw_stage_list
	)
```
This performs power estimation.

Function `image_pipeline_noise_simulation_example` and `eventification_noise_simulation_example`
are two different noise modeling simulations. `image_pipeline_noise_simulation_example` is a common 
imaging pipeline inside the sensor, and it calls our default simulation launch function. 
`eventification_noise_simulation_example` is a more complex example, the computation has a complex 
data dependency graph, which needs users to define a cunstomized simulation function. 

after those functions are defined, just run `example_run.py`
```
 $ python3 example_run.py 
```
You will see the simulation is running!
