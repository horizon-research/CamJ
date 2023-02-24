# CamJ: An Energy Modeling and System-Level Exploration Framework for In-Sensor Visual Computing

CamJ is an in-sensor processing simulation Framework. CamJ allows image sensor designers to quickly evaluate
the energy of their designs in minutes. CamJ provides commonly-used sensor design blocks, both analog and digital,
which allow users to describe the designs using a declarative interface in Python.

## Code Organization

CamJ has two core modules that drive in-sensor simulation: power/energy estimation and functional 
simulation (noise modeling). We put these two core modules into these two directories:

- `camj`: the main source code of CamJ.
- `tutorial`: a tutorial walking you through the CamJ APIs and showing you how to use CamJ to model a concrete computational image sensor and obtain energy consumption estimations.
- `utility`: useful tools, e.g., generating noise-free images (input to CamJ) from RGB images.
- `examples`: examples we built that use CamJ to model existing (computational) image sensors and validate against published results.
- `tests`: test cases.
- `test_imgs`: sample inputs to CamJ, i.e., noise-free images.

## Design Philosophy

To use our framework, users need to specify the sensor configuration using CamJ API. CamJ API provides
three major parts to allow users freely describe their designs and the software  or the algorithms
that are running on their sensor designs. The followings are the brief descriptions of the three parts:

- software configuration: this file describes how algorithms are runnning in software. Our assumption
about the software pipeline is that the image pipeline can be described as a directed acyclic graph (DAG).
Therefore, we design CamJ API so that each node is a processing stage and each connection is the data 
dependency. On each node, we constrain computations to be stencil operations, which is most commonly
used operation in image/graph processing.
- hardware desription: this file describes the hardware configuration. Similar to writing designs in
HDL, users need to describe both processing units and memory structures. However, CamJ abstract some 
commonly-used hardware structures in sensor designs so that users only need to describes their designs
using built-in high-level hardware components.
- software-to-hardware mapping function: this part describes how to map software computation stages
to hardware components.

Here shows the overview of our system. For more details, please refer our [paper]().

![camj](https://user-images.githubusercontent.com/21286132/216838473-c1477396-f1f6-4b04-a14b-7292c32948ad.png)


## Tutorial

In [`tutorial`](https://github.com/horizon-research/in-sensor-simulator/tree/main/tutorial) subdirectory,
we have a simple example and a step-by-step explanation of implementing 
a simple imaging pipeline using CamJ API. Please check out [`tutorial`](https://github.com/horizon-research/in-sensor-simulator/tree/main/tutorial) directory for more details.

## To run Existing Examples

Directory `examples` contains several examples that we use for validation in our paper. Here, we use
`ieee_vr22` as an example to show how to run our program. In `ieee_vr22` folder, `sw_pipeline.py` 
describes the software dataflow, `hw_config` and `analog_config.py` describes hardware configuration
and `mapping_file.py` describes the mapping mechanism between software stages and hardware units. 

In `example_run.py`, it contains how to use CamJ API to run simulation. `run_ieee_vr22()` function shows
an example how to include user-defined hardware configurations and feed to CamJ simulator.
First, we includes software/hardware configuration files which are defines using CamJ API. To know 
more about how to set software/hardware configurations, please check out [ieee_vr22](https://github.com/horizon-research/in-sensor-simulator/tree/main/ieee_vr22).

```python
from ieee_vr22.mapping_file import mapping_function
from ieee_vr22.sw_pipeline import sw_pipeline
from ieee_vr22.hw_config import hw_config
```

Next, get the major configurations for sensor simulation, as shown below.
```python
hw_dict = hw_config()
mapping_dict = mapping_function()
sw_stage_list = sw_pipeline()
```

To understand how to configure hardware and software pipeline please refer [sim_core](https://github.com/horizon-research/in-sensor-simulator/tree/main/sim_core) directory. If you want to understand more about noise modeling in CamJ, please refer [functional_core](https://github.com/horizon-research/in-sensor-simulator/tree/main/functional_core).

Next, based on what we want to simulate, this example shows both energy simulation and functional 
simulation. The following function runs power/energy simulation:
```python
launch_simulation(
	hw_dict = hw_dict,
	mapping_dict = mapping_dict,
	sw_stage_list = sw_stage_list
)
```

Function `eventification_noise_simulation_example` shows how to run noise modeling simulations. 
In this example, it first runs noise modeling for an common sensor imaging pipeline. 
Then, the noising image will feed to a special hardware to generate events between two temporally-adjacent
images. In this example, we also show how CamJ accepts builtin hardware components and also any customized
hardware components. For more details, please check out `ieee_vr22` and `functional_core` directory.

After those functions are defined, just run `example_run.py`
```
 $ python3 example_run.py 
```
You will see the simulation is running!

