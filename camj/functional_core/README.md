# Functional-Core

This is the core library for functional (noise) modeling in CamJ framework.

## Structure of This Library

There are two parts inside this directory. The core noise modeling implementation is in 
`noise_model.py` and `launch.py`. Another part of this directory contains algorithm pipeline that 
can reverse a regular RGB image to a raw image (inside `reverse_process.py`) and corresponding 
forward processing pipeline (`forward_process.py`). 

## Noise Modeling

CamJ provides some built-in classes for modeling noise inside photodiode, floating diffusion, \
correlated double sampling and many more. To construct a class, for example, a noise model for photodiode (PD):

```
# PD parameters
dc_noise = 2.5 # electrons
pixel_full_well_capacity = 10000 # e
dcnu_std = 0.001

pd_noise = PhotodiodeNoise(
	"Photodiode",
	dark_current_noise=dc_noise,
	max_val=pixel_full_well_capacity,
	enable_dcnu=True,
	dcnu_std=dcnu_std,
)
```

This example shows how to construct a PD. In this example, PD has a dark current noise with an average 
value of 2.5 e. The maximum value of one PD can store is 10000 e. Any value greater than 10000 is 
clipped during the simulation. `enable_dcnu` and `dcnu_std` are two parameters to enable modeling 
dark current non-uniformity (DCNU). In this case, dark current noise follows a normal distribution 
with a standard deviation of 0.001x2.5 and will be random-sampled during noise modeling.

In addition to some built-in noise classes for key sensor components. CamJ also provides two generic 
classes, `PixelwiseNoise` and `ColumnwiseNoise`, for users to define a range of sensor components 
that follow the same noise model.

Here is an example to use `PixelwiseNoise` to model a source follower.

```
# SF parameters
sf_read_noise = 0.0007 # V
sf_gain = 1.0
sf_prnu_std = 0.001

sf_noise = PixelwiseNoise(
	name = "SourceFollower",
	gain = sf_gain,
	noise = sf_read_noise,
	max_val = 1.2, #V
	enable_prnu = True,
	prnu_std = sf_prnu_std
)
```

In this example, we model a source follower (SF) which has gain of 1.0 and read noise 0.00007 V. 
In addition, we also model the pixel response non-uniformity (PRNU) of SF. PRNU is specified by 
`enable_prnu` flag and `prnu_std` which is the standard deviation of SF gain.

## How to Run

To run functional simulation, we need to first build a complete functional pipeline that represents
the functionality of the analog stage. In `ieeevr_22/functional_pipeline.py`. we show two such examples.
In these two examples, `sensor_functional_pipeline` constructs a typical sensor imaging pipeline, 
`eventification_functional_pipeline` constructs a pipeline that can perform eventification (see 
IEEE VR 22 [paper](https://horizon-lab.org/pubs/vr22.pdf) for more details). 

After the functional pipeline is defined. We need to assign the functional pipeline to the corresponding
analog hardware unit. here, we define assign the `sensor_functional_pipeline` to an `AnalogArray` 
object named `PixelArray`. Later on, when CamJ performs functional simulation, CamJ will use this
particular functional pipeline with our default functional simulation routine.

```

pixel_array = AnalogArray(
	name = "PixelArray",
	layer = ProcessorLocation.SENSOR_LAYER,
	num_input = [(640, 2, 1)],
	num_output = (320, 1, 1),
	functional_pipeline = sensor_functional_pipeline()
)
```

However, current CamJ functional simulation routine only supports the functional pipeline without 
branches. For more complex functional simulation, users need to provide a customized functional 
simulation routine. How to define a customized functional simulation routine. Please check out 
function `customized_eventification_simulation` in `functional_core/launch.py` for more details.

To use a customized functional simulation routine, we need to define this function in hardware analog
configuration.

```
eventification_array = AnalogArray(
	name = "EventificationArray",
	layer = ProcessorLocation.SENSOR_LAYER,
	num_input = [(320, 1), (320, 1)],
	num_output = (320, 1),
	functional_pipeline = eventification_functional_pipeline(),
	functional_sumication_func = customized_eventification_simulation
)
```
Here in this `EventificationArray`, we define its attribute `functional_simulation_func` to be 
`customized_eventification_simulation`. Please see `functional_core/launch.py` to see how to define 
a customized functional simulation function.
