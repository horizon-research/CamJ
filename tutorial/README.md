# Tutorial

The best way to learn how to use CamJ is to go through this tutorual.
We show you, step-by-step, how to use CamJ APIs to describe a simple computational CIS, both its software and hardware,
and then perform functional (noise) and energy simulations.

## How to Run

It's a good idea to run the tutorial first and see what it does. We will then explain how it does it.

To run the example in this tutorial, simply do:
```
python3 tutorial_run.py
```

You will see two things: a new window showing an image and a bunch of statistics dumped in your terminal. The image shown in the window is the image captured by the CIS (after the ADC) you create in this example. That image is noisy, because the imaging process is noisy; one main goal of CamJ is to accurately capture the noises introduced by the CIS, which we will discuss later.

The terminal will show the following statistics, which is a component-level breakdown of the energy consumption per pixel.

```
CamJ output
```

Pressing any key destroys the window and exits the program.

## The Code Entry Point

The script `tutorial_run.py` shows how to run this simple example. First, we import the configuration
files:
```python
# import tutorial example configuration modules
from tutorial.mapping_file import mapping_function
from tutorial.sw_pipeline import sw_pipeline
from tutorial.hw_config import hw_config
```
Next, we load the configuration setting into the `main` program.
```python
hw_dict = hw_config()
mapping_dict = mapping_function()
sw_stage_list = sw_pipeline()
```
In this tutorial, we show both functional simulation and energy simulation. `tutorial_functional_simulation`
corresponds to functional simulation and `launch_simulation`.

In `tutorial_functional_simulation`, we first load the image into the program and then converts the 
image into proper input format, in this case, we convert a grayscale image into photon based on the
sensor settings that we use in hardware configuration file. Put `photon_input` array into a dictionary
which CamJ simulator will use later. The keyword `Input` in the dictionary corresponds to the name 
of the software stage which uses `phonton_input` as input:
```python
# sensor specs
full_scale_input_voltage = 1.2 # V
pixel_full_well_capacity = 10000 # e

# load test image
img = np.array(cv2.imread(img_name, cv2.IMREAD_GRAYSCALE))
# a simple inverse img to photon
photon_input = img/255*pixel_full_well_capacity

input_mapping = {
    "Input" : [photon_input]
}
```
Next, feed `input_mapping` with other configuration structures to a default functional simulation 
function called `launch_functional_simulation`. The output of `launch_functional_simulation` is dictionary.
Every key in this dictionary is a software stage name and the corresponding value is the simulation 
output of the software stage (in a form of list, because it might contains multiple outputs). We can 
inspect the result using OpenCV `imshow` function:
```python
simulation_res = launch_functional_simulation(sw_stage_list, hw_dict, mapping_dict, input_mapping)

img_after_adc = simulation_res['Input'][0]

cv2.imshow("image after adc", img_after_adc/np.max(img_after_adc))
cv2.waitKey(0)
cv2.destroyAllWindows()
```


You will be able to run both functional simulation and power simulation!

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

```python
input_data = PixelInput((32, 32, 1), name="Input")
```

Use CamJ `PixelInput` API, and set the pixel input size. This will do the work!

Next, we define the first computation stage of the software pipeline, `Conv`:

```python
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

```python
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

```python
conv_stage.set_input_stage(input_data)
abs_stage.set_input_stage(conv_stage)
```

In the end, we need to put every computational stage into a single list and return to `CamJ` simulator:

```python
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

```python
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

```python
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

```python
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
```python

fifo_buffer1 = FIFO(
    name="FIFO-1",
    hw_impl = "sram",
    count = 32*32,
    clock = 500,    # MHz
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
    clock = 500,    # MHz
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
    clock = 500,    # MHz
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

```python
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

```python
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
generated during analog computing process. Since digital computing is always precise if we assume no
hardware error happens.

In `analog_config.py`, we define two analog compoenents called `Pixel` and `ColumnAmplifier`. Inside
`Pixel` instance, we add `ActivePixelSensor`, here, we show the detailed definition of `ActivePixelSensor`:

```python
ActivePixelSensor(
    # performance parameters
    pd_capacitance = 1e-12,
    pd_supply = 1.8, # V
    output_vs = 1, #  
    enable_cds = False,
    num_transistor = 3,
    # noise model parameters
    dark_current_noise = 0.005,
    enable_dcnu = True,
    enable_prnu = True,
    dcnu_std = 0.001,
    fd_gain = 1.0,
    fd_noise = 0.005,
    fd_prnu_std = 0.001,
    sf_gain = 1.0,
    sf_noise = 0.005,
    sf_prnu_std = 0.001
)
```

As the comment shows, there are a few input parameters define the noide model of this instance. For 
instance, `dark_current_noise` and `enable_dcnu` set the average dark current noise and enable DCNU.
`fd_gain` set the floating diffusion (FD) gain is 1. `fd_noise` sets FD read noise. `enable_prnu` 
and `fd_prnu_std` set to enable simulate PRNU of FD and the standard deviation of FD is 0.001. Same
as `sf`-related parameters which configure source follower inside pixel.

```python
ColumnAmplifier(
    load_capacitance = 1e-12,  # [F]
    input_capacitance = 1e-12,  # [F]
    t_sample = 2e-6,  # [s]
    t_frame = 10e-3,  # [s]
    supply = 1.8,  # [V]
    gain = 1,
    # noise parameters
    noise = 0.005,
    enable_prnu = True,
    prnu_std = 0.001,
)
```

Here, we show how to configure a column amplifier. Noise-related parameters are:
* `noise`: defines the average read noise of column amplifier
* `enable_prnu`: enable PRNU on column amplifier gain.
* `prnu_std`: set the standard deviation of PRNU.



















