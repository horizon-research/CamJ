# Tutorial

This README gives a simple yet complete example of how to define each part (software/hardware) 
configuration using CamJ API. By going through this example, you will be able to define a image sensor
and perform both functional and power simulation using CamJ!

## Structures

To configure a complete sensor system, users need to define following configuration files:

| File Name             | Functionality                                 |
|-----------------------|-----------------------------------------------|
| sw_pipeline.py        | the dataflow in the software pipeline         |
| analog_config.py      | the hardware configuration in analog domain   |
| hw_config.py          | the hardware configuration in digital domain  |
| mapping_file.py       | the mapping between hardware and software     |

Next, we introduce each configuration file piece by piece,

## Software Configuration

In this example, we define a simple image pipeline, but this example can touch most of CamJ API. The
list below shows the stages inside this software pipeline.

| Stage Name | Description                                   |
|------------|-----------------------------------------------|
| Input      | defines a 32x32x1 pixel input                 |
| Conv       | defines a 3x3x1 convolution with stride of 1  |
| Abs        | defines a element-wise absolute               |

`Input` is used to define the initial input of the software pipeline. To define software pipeline 
input is simple:

```
input_data = PixelInput((32, 32, 1), name="Input")
```

Use CamJ `PixelInput` API, and set the pixel input size. This will do the work!

Next, we define the first computation stage of the software pipeline, `Conv`:

```
conv_stage = ProcessStage(
	name = "Conv",
	input_size = [(32, 32, 1)],
	kernel_size = [(3, 3, 1)],
	stride = [(1, 1, 1)],
	output_size = (32, 32, 1),
	padding = [Padding.ZEROS]
)
```

In CamJ, we assume every operations are stencil operations, to define a non-DNN operation, we can 
use `ProcessStage` API. Here, we define the convolution kernel is `3x3x1` with input size `32x32x1`. 
The reason we define the input to be a list of tuples is that `ProcessStage` can potentially take 
multiple data as input. Also, we need to define stride which is `1x1x1` and the padding of the input.
Here the padding is zero-padding to make sure the output size is also `32x32x1`. Lastly, we define 
the output size to be `32x32x1`. This would complete the definition of `Conv` stage.

Similarly, we define a `Abs` operation. This `Abs` operation compute the element-wise absolution. The
definition is similar to `Conv` operation. Here, the input and output size are both `32x32x1`. The 
stride is `1x1x1` and the padding is `NONE` to make sure that the output size is still `32x32x1`.

```
abs_stage = ProcessStage(
	name = "Abs",
	input_size = [(32, 32, 1)],
	kernel_size = [(1, 1, 1)],
	stride = [(1, 1, 1)],
	output_size = (32, 32, 1),
	padding = [Padding.NONE]
)
```

This would define all the stages in the software pipeline. In addtion to define each stage in the 
software pipeline, we also need to define the connection in the software pipeline. Here, we show the 
connection:

```
conv_stage.set_input_stage(input_data)
abs_stage.set_input_stage(conv_stage)
```

In the end, we need to put every computational stage into a single list and return to `CamJ` simulator:

```
sw_stage_list.append(input_data)
sw_stage_list.append(conv_stage)
sw_stage_list.append(abs_stage)

return sw_stage_list
```

This will finish software definition!

## Hardware configuration

hardware configuration contains two parts: analog configuration and digital configuration, we will 
introduce them one-by-one.

### Analog configuration

Here, we just need to define one analog strcuture which is pixel array itself.

```
pixel_array = AnalogArray(
	name = "PixelArray",
	layer = ProcessorLocation.SENSOR_LAYER,
	num_input = [(32, 1, 1)],
	num_output = (32, 1, 1),
)
pixel = AnalogComponent(
    name = "Pixel",
    input_domain =[ProcessDomain.OPTICAL],
    output_domain = ProcessDomain.VOLTAGE,
    component_list = [
        (
            ActivePixelSensor(
                ...
            ),
            1
        )
    ],
    num_input = [(1, 1)],
    num_output = (1, 1)
)

col_amp = AnalogComponent(
    name = "ColumnAmplifier",
    input_domain =[ProcessDomain.VOLTAGE],
    output_domain = ProcessDomain.VOLTAGE,
    component_list = [
        (
            ColumnAmplifier(
                ...
            ),
            1
        )
    ],
    num_input = [(1, 1)],
    num_output = (1, 1)
)
```

To define an analog structure in CamJ, users first need to define a `AnalogArray` which serves as a 
template to contain smaller structures which are called `AnalogComponent`. Here, we first define 
`PixelArray`. For this `PixelArray`, we don't need to define the input and output size but input/output
throughput. Here, the input and the output throughput are both `32x1x1`. This mimics the rolling shutter
effect.

After we define the analog array template, we need to define the component inside this analog array.
Here, this example shows the pxiel input domain is `OPTICAL` and output domain is `VOLTAGE`. To deine
the input and output domain allows CamJ to check if the connections between different analog components
are correct. Then, we define the energy function of this analog compoenent. Here, we use a CamJ 
builtin template to define an 3T active pixel sensor (3T-APS). We use a list of tuple here, because 
one analog component might includes more than one analog structures. `1` in the second element of this 
tuple shows that only one 3T-APS inside this analog component.

Additionally, we also need to define a column amplifier in the pixel array for pixel readout. Here,
`col_amp` instance is a column amplifer component. Both the input and the output domain of column 
amplifier are `VOLTAGE`.

```
pixel_array.add_component(pixel, (32, 32, 1))
pixel_array.add_component(col_amp, (32, 1, 1))

analog_arrays.append(pixel_array)

return analog_arrays
```

After we define pxiel array and pixel components, we need to add pixel components (both pixel and 
column amplifier) to the pixel array using `add_component` function. Next, we need to define the 
connection between different analog arrays. Here, we only have one analog array, so no need to define 
the connection across different analog arrays. 

Last, we add every analog array to a `analog_arrays` list and return to CamJ simulator.

### Digital Configuration

Here, we define two digital components that supports both convolution and absolute operations in 
software pipeline.

```
conv_unit = ComputeUnit(
 	name="ConvUnit",
	domain=ProcessDomain.DIGITAL,
	location=ProcessorLocation.SENSOR_LAYER,
	input_throughput = [(32, 3, 1)],
	output_throughput = (32, 1, 1), 
	clock = 500, # MHz
	energy = XX,
	area = XX,
	initial_delay = 0,
	delay = 3,
)

abs_unit = ComputeUnit(
 	name="AbsUnit",
	domain=ProcessDomain.DIGITAL,
	location=ProcessorLocation.SENSOR_LAYER,
	input_throughput = [(32, 1, 1)],
	output_throughput = (32, 1, 1), 
	clock = 500, # MHz
	energy = XX,
	area = XX,
	initial_delay = 0,
	delay = 3,
)

```

Here, we define two compute units using CamJ API, `ComputeUnit`. In `ComputeUnit`, we need to define 
input and output throughput and number of delay to finish compute such number of elements. Here, we 
show that `ConvUnit` input throughput is `32x3x1` and its output throughput is `32x1x1`. The time to
compute those elements is 3 cycles. Also, we show the corresponding energy consumption to output those 
element. `location` attribute is used to define where this compute unit is.

After we define the compute components in digital domain, we also need to define the memory buffer 
between two compute units. Here, we define three line buffers. The first line buffer is used between 
pixel sensor readout and `ConvUnit`. The second line buffer is used to save the result from `ConvUnit` 
and read by `AbsUnit`. The last line buffer is used to save the result from `Absunit`. Here is the 
definition of these three memory structures:
```

fifo_buffer1 = FIFO(
	name="FIFO-1",
	hw_impl = "sram",
	count = 32*32,
	clock = 500, 	# MHz
	write_energy = 3,
	read_energy = 1,
	location = ProcessorLocation.COMPUTE_LAYER,
	duplication = 100,
	write_unit = "ADC",
	read_unit = "ConvUnit"
)

fifo_buffer2 = FIFO(
	name="FIFO-2",
	hw_impl = "sram",
	count = 32*32,
	clock = 500, 	# MHz
	write_energy = 3,
	read_energy = 1,
	location = ProcessorLocation.COMPUTE_LAYER,
	duplication = 100,
	write_unit = "ConvUnit",
	read_unit = "AbsUnit"
)

fifo_buffer3 = FIFO(
	name="FIFO-3",
	hw_impl = "sram",
	count = 32*32,
	clock = 500, 	# MHz
	write_energy = 3,
	read_energy = 1,
	location = ProcessorLocation.COMPUTE_LAYER,
	duplication = 100,
	write_unit = "AbsUnit",
	read_unit = "AbsUnit"
)
```

All three line buffers have the size of `32x32`. Their read and write energy are 1 and 3 pJ, respectively.
Also, we need to define the access unit for each line buffer. The compute unit that does not have the 
permission to access the memory structure is not able to access the memory structure.

Last, we define the connection between memory structures and compute units by using `set_input_buffer`
and `set_output_buffer`:

```
adc.set_output_buffer(fifo_buffer1)

conv_unit.set_input_buffer(fifo_buffer1)
conv_unit.set_output_buffer(fifo_buffer2)

abs_unit.set_input_buffer(fifo_buffer2)
abs_unit.set_output_buffer(fifo_buffer3)

```

This will finish defining the hardware configuration!

## Mapping between Software and Hardware

To define the mapping between hardware and software is quite simple. We just need to define a dictionary
and each key is the software stage names and values are the hardware component names.

```
mapping = {
	"Input" : "PixelArray",
	"Conv" : "ConvUnit",
	"Abs" : "AbsUnit",
}
```

---

### To this point, if you just want to perform energy simulation, you can stop here. If you want know more about the functional simulation of CamJ, please continue.

---

## Functional Simulation

CamJ supports analog functional simulation. The purpose of functional simulation is to mimic the noise
generated during analog computing process. Since digital computing is always precise if we assume no hardware error happens.

In `functional_pipeline.py`, we define a noise model for sensor imaging pipeline. In this pipeline, 
we assume following pipeline: photodiode (PD) -> floating diffusion (FD) -> source follower (SF) -> 
column amplifier (CA) -> correlated double sampling (CDS) -> analog-to-digital convertor (ADC).

For some analog components, we have specific templates to describe the hardware, for instance, PD, 
FD and ADC. Here is an example of defining PD:
```
pd_noise = PhotodiodeNoise(
	"Photodiode",
	dark_current_noise=dc_noise,
	max_val=pixel_full_well_capacity,
	enable_dcnu=True,
	dcnu_std=dcnu_std,
)
```

Here, we define a PD noise model with dark current and dark current non-uniformity (DCNU). You can 
check `functional_pipeline.py` for FD and ADC definition.

In addition to specific templates, we also provide some general templates that can fit a broad range
of analog components. Here is an example to use CamJ `PixelwiseNoise` template to define a SF:
```
sf_noise = PixelwiseNoise(
	name = "SourceFollower",
	gain = sf_gain,
	noise = sf_read_noise,
	max_val = pixel_full_well_capacity*conversion_gain,
	enable_prnu = True,
	prnu_std = sf_prnu_std
)
```
Because SF noise applies to individual pxiels and each pixel can potential have different pixel
responses, which we call it pixel response non-uniformity (PRNU). Here, we also define to enable PRNU
during the simulation.

In comparison, CA is shared for the entire column of pixels, CamJ provides another template called 
`ColumnwiseNoise` to define CA:
```
col_amplifier_noise = ColumnwiseNoise(
	name = "ColumnAmplifier",
	gain = column_amplifier_gain,
	noise = col_amp_read_noise,
	max_val = pixel_full_well_capacity*conversion_gain*column_amplifier_gain,
	enable_prnu = True,
	prnu_std = col_amp_prnu_std
)
```

After we define each analog component in the imaging pipeline, we add every component into a list 
*IN ORDER* and return to CamJ simulator.

```
...
functional_pipeline_list.append(adc_noise)

return functional_pipeline_list
```

## How to Run

How to run CamJ simulation for this example is quite simple. In the root directory, we have a running
script called `tutorial_run.py`. Run this script:
```
 $ python3 tutorial_run.py
```

You will be able to run both functional simulation and power simulation!


















