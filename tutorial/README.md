# Tutorial

The best way to learn how to use CamJ is to go through this tutorual.
We show you, step-by-step, how to use CamJ APIs to describe a simple computational CIS, both its software and hardware,
and then perform functional (noise) and energy simulations.

## Run It

It's a good idea to run the tutorial first and see what it does. We will then explain how it does it.

To run the example in this tutorial, simply do:
```
python3 tutorial_run.py
```

You will see two things: a new window showing an image and a bunch of statistics dumped in your terminal. The image shown in the window is the image captured by the CIS (after the ADC) you create in this example. That image is noisy, because the imaging process is noisy; one main goal of CamJ is to accurately capture the noises introduced by the CIS, which we will discuss later.

The terminal will show the following statistics, which is a component-level breakdown of the energy consumption per pixel.

```
[Summary]
Overall system cycle count:  1354
[Cycle distribution] {Input: 96, Conv: 896, Abs: 448}
ADC total_cycle:  32 total_write:  1024 total_read:  0 total_compute_energy: 19200 pJ total_comm_energy: 4198 pJ
ConvUnit total_cycle:  768 total_write:  8192 total_read:  3072 total_compute_energy: 36864 pJ total_comm_energy: 46182 pJ
AbsUnit total_cycle:  256 total_write:  8192 total_read:  8192 total_compute_energy: 4096 pJ total_comm_energy: 67174 pJ
[End] Digitial Simulation is DONE!
(181574.38905275147,
 {'PixelArray': 3860.3890527514923,
  'ADC': 23398,
  'ConvUnit': 83046,
  'AbsUnit': 71270})
```

## Code Walk-Through

In `tutorial_run.py`, `launch_simulation()` is the CamJ API that performs the energy simulation of a CIS. Follow how it's defined and what parameters it needs to understand how CamJ simulation works. Briefly, in order for CamJ to perform energy simulation, we need to specify three pieces of information: 1) the hardware description, 2) the algorithm description, and 3) algorithm to hardware mapping. They are `hw_dict`, `sw_stage_list`, and `mapping_dict` in the `launch_simulation` interface:

```python
launch_simulation(hw_dict, mapping_dict, sw_stage_list)
```

### Software Description

This CIS executes a simple software pipeline, which is described in `sw.py` and has three stages:

| Stage Name | Description                                   |
|------------|-----------------------------------------------|
| Input      | defines a 32x32x1 pixel input                 |
| Conv       | defines a 3x3x1 convolution with stride of 1  |
| Abs        | defines a element-wise absolute               |

In CamJ, any software pipeline starts with an input image, which is created by instaitiating a [`PixelInput`]() object in CamJ below, which says the pixel array captures a 32x32 image.
The naming convention in CamJ is that all the natively-supported hardware structures (compute and memory, analog and digital) are defined as UpperCamelCase-named classes.

```python
input_data = PixelInput((32, 32, 1), name="Input")
```

This raw pixel array is then sent through two sequential processing stages, one performing a simple 3x3 convolution and the other performing an element-wise absolute operation. We observe that image processing algorithms can be abstracted as stencil operations
that operate on a local window of pixels at a time.
An element-wise stage is nothing more than a 1x1 stencil stage.

Therefore, users express only the input/output image dimensions (`input_size`, `output_size`) along with the
stencil window (`kernel_size`) and stride size (`stride`).
Given the regular computation and data access pattern of stencil operations, CamJ could accurately estimate the access
counts to different hardware structures for energy estimations.

For instance, the convolution stage is described as:

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

The `abs_stage` is similarly defined, but note that the `stride` is `[(1, 1, 1)]`.

We connect the software stages together:

```python
conv_stage.set_input_stage(input_data)
abs_stage.set_input_stage(conv_stage)
```

In the end, we need to put every stage into a single list used by `launch_simulation()`:

```python
sw_stage_list.append(input_data)
sw_stage_list.append(conv_stage)
sw_stage_list.append(abs_stage)

return sw_stage_list
```

### Hardware Description

In this tutorial example, `hw_dict` is defined in `hw.py`. CamJ requires the hardware description of a CIS to be a dictionary with three keys, each of which accepts an array as its value:

```python
hw_dict = {
  "memory" : [], # to be added later
  "compute" : [], # to be added later
  "analog" : analog_config() # defined and added in analog.py
}
```

The three members represent the digital memory structures, digital compute units, and analog units. Let's see how each is described.

#### Digital Compute Units

Our CIS needs three digital units, starting with an ADC created as an CamJ `ADC` object, and two compute units for the convolution and absolute operations in the software pipeline.
The two compute units are instantiated as two CamJ [`ComputeUnit`]() objects.

```python
conv_unit = ComputeUnit(
    name="ConvUnit",
    domain=ProcessDomain.DIGITAL,
    location=ProcessorLocation.SENSOR_LAYER,
    input_throughput = [(32, 3, 1)],
    output_throughput = (32, 1, 1), 
    clock = 500, # MHz
    energy = 32*9*compute_op_power,
    area = 30,
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
    energy = 32*compute_op_power,
    area = 10,
    initial_delay = 0,
    delay = 3,
)
```

In `ComputeUnit`, we need to define the input and output throughput of that unit. The input throughput means the number of elements that must be ready before the unit can start processing. The output throughput is the number of output elements generated given that many input elements.
We also need to specify a `delay` attribute, which indicates the number of cycles it takes to process that many input elements.

For instance, `ConvUnit` has an input throughput of `32x3x1` and an output throughput of `32x1x8`.
It takes 3 cycles to finish processing that many elements.

In addition, CamJ also requires programmers to specify the clock rate and the per operation energy of each compute unit. The `location` attribute is used to define where this compute unit is.

#### Digital Memory Units

In this example, we will need three line bufferes as the digital memories. We create them by instantiating three CamJ [`LineBuffer`]() objects.

The first line buffer is used between pixel sensor readout and `ConvUnit`.
The second line buffer is used to save the result from `ConvUnit` and read by `AbsUnit`.
The last line buffer is used to save the result from `Absunit` and will eventually be transferred out of the CIS.

Here is the  definition of these three memory structures:
```python
line_buffer = LineBuffer(
    name="LineBuffer",
    hw_impl = "sram",
    size = (3, 32),
    clock = 500,    # MHz
    write_energy = 3,
    read_energy = 1,
    location = ProcessorLocation.COMPUTE_LAYER,
    duplication = 1,
    write_unit = "ADC",
    read_unit = "ConvUnit"
)

fifo_buffer1 = FIFO(
    name="FIFO-1",
    hw_impl = "sram",
    count = 3*32,
    clock = 500,    # MHz
    write_energy = 3,
    read_energy = 1,
    location = ProcessorLocation.COMPUTE_LAYER,
    duplication = 8,
    write_unit = "ConvUnit",
    read_unit = "AbsUnit"
)

fifo_buffer2 = FIFO(
    name="FIFO-2",
    hw_impl = "sram",
    count = 3*32,
    clock = 500,    # MHz
    write_energy = 3,
    read_energy = 1,
    location = ProcessorLocation.COMPUTE_LAYER,
    duplication = 8,
    write_unit = "AbsUnit",
    read_unit = "AbsUnit"
)
```

All three line buffers have a size of `32x3`, that is, 3 lines each storing 32 pixels.
The per-read and per-write energy consumption is 1 pJ and 3 pJ, respectively.

Also, we need to define the access unit for each line buffer. The compute unit that does not have the 
permission to access the memory structure is not able to access the memory structure.

Last, we define the connections between memory structures and compute units by using `set_input_buffer`
and `set_output_buffer`:

```python
adc.set_output_buffer(line_buffer)

conv_unit.set_input_buffer(line_buffer)
conv_unit.set_output_buffer(fifo_buffer1)

abs_unit.set_input_buffer(fifo_buffer1)
abs_unit.set_output_buffer(fifo_buffer2)
```

#### Analog Hardware (Compute and Memory)

The analog hardware is a bit more complicated, so we create them in a separate file `analog.py`. The hardware in the analog domain consists of a set of `AnalogArray`s. In our CIS, the only analog array we need is the `PixelArray`. Its input and output throughputs are both `32x1x1`, mimicking a rolling shutter sensor.

```python
pixel_array = AnalogArray(
    name = "PixelArray",
    layer = ProcessorLocation.SENSOR_LAYER,
    num_input = [(32, 1, 1)],
    num_output = (32, 1, 1),
)
```

Each `AnalogArray` consists of a set of [`AnalogComponent`]()s. In our CIS, the pixel array has two types of [`AnalogComponent`]()s, 32x32 `pixel`s and 1x32 `col_amp`s (column amplifiers).

The `pixel` component's input is in the `OPTICAL` domain and its output is in the `VOLTAGE` domain.
Specifying the input and output domains allows CamJ to check if the connections between different analog components are correct.
The specific pixel technology we want to use in this CIS is a 3T active pixel sensor (3T-APS), which is instantiated through the [`ActivePixelSensor`]() class.
The 3T-APS is then added to the `component_list`, which is an array, indicating that there could be multiple sub-components in a component.
Each sub-component is a tuple, where the second element indicates the number of sub-components in a component. For instance, `1` here means we have only one 3T-APS inside a pixel.

```python
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
```

`col_amp` is a column amplifer component. Both the input and the output domain of the column amplifier are `VOLTAGE`.

```python
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

The two types of components are added to the pixel array, which is then added to the analog hardware description, which is eventually returned.

```python
pixel_array.add_component(pixel, (32, 32, 1))
pixel_array.add_component(col_amp, (32, 1, 1))

analog_arrays.append(pixel_array)
```

### Mapping

To define the mapping between hardware and software is quite simple. We just need to define a dictionary
and each key is the software stage name and the value is the hardware component name. The software and hardware component names are the values of the `name` variable when creating the corresponding CamJ objects.

In our example, the mapping is defined in `mapping_file.py`:

```python
mapping = {
    "Input" : "PixelArray",
    "Conv" : "ConvUnit",
    "Abs" : "AbsUnit",
}
```

## Functional (Noise) Simulation

In addition to energy simulation, CamJ also models the noises introduced in the CIS hardware. Noise simulation is important for architectural exploration. For instance, using a 3D stacking CIS design would increase the data communication bandwidth (between the pixel array and the compute units) and allow for [heterogeneous integration](https://www.eetimes.eu/heterogeneous-integration-and-the-evolution-of-ic-packaging/), but might also increase the temperature, which increases thermal-induced noises (e.g., read noise, dark-current noise). Noise simulation allows us to evaluate the energy-vs-task quality trade-offs when making hardware design decisions.

In CamJ, noise simulation is also called functional simulation, and is performed using the following API:

```python
launch_functional_simulation(sw_stage_list, hw_dict, mapping_dict, input_mapping)
```

As you can see, noise simulation requires the three parameters needed for energy simulation, along with an addtional parameter: the input image.
Calling it an input image is a bit confusing, because it's not really an image. Rather, it's the map of the electron counts after an exposure stored in each photo-diode (before any read out).
In theory, the electron count map is obtained by simulate the light transport in the physical scene and the camera optics, but CamJ currently doesn't do that, so we emulate it by directly requiring an raw electron count map as the input. We are working on integrating CamJ with tools like [ISET3d](https://github.com/ISET/iset3d) or [PBRT](https://github.com/mmp/pbrt-v4) to obtain an actual electron map with physics simulations.

### Creating Electron Map

We create a electron map by reading a gray-scale image and convert pixel values to electron counts based on the full-well capacity of the CIS.

```python
# sensor specs
full_scale_input_voltage = 1.8 # V
pixel_full_well_capacity = 10000 # e

# load test image
img = np.array(Image.open(img_name).convert("L"))
# a simple inverse img to electrons
electron_input = img/255*pixel_full_well_capacity

input_mapping = {
    "Input" : [electron_input]
}
```

The gray-scale image is used as a container for raw electron counts. So it's your responsibility to make sure the pixel values are proportional to electron counts. Gray-scale downloaded from the Internet most likely won't be that. If you have a RGB image, there is a script under `utility` folder that reverses the ISP pipeline and generates a raw pixel map.

### Noise Simulation Outputs

The output of `launch_functional_simulation` is a dictionary.
Every key in this dictionary is a software stage name and the corresponding value is the simulated 
output of that software stage.
Note that the output of each stage is a list, because a stage might contains multiple outputs.

For instance, we can look at the image generated after the ADC:

```python
img_after_adc = simulation_res['Input'][0]
img_res = Image.fromarray(np.uint8(img_after_adc / full_scale_input_voltage  * 255) , 'L')
```

### Noise Modeling Details

The noise model that CamJ uses is described in detail [here](https://www.cs.rochester.edu/courses/572/fall2022/decks/lect11-noise-color-sensing.pdf#page=65). Briefly, it considers both temporas noise and fixed-pattern noise (FPN). Temporal noise includes photon shot noise, dark-current noise, and read noise. FPN includes dark signal non-uniformity (DSNU) and photon response non-uniformity (PSNU).

CamJ allows programmers to specify a set of noise-related attributes when creating an analog component. For instance in `analog_config.py`, the `ActivePixelSensor` and `ColumnAmplifier` are instantiated as follows:

```python
ActivePixelSensor(
    # latency and performance parameters
    pd_capacitance = 1e-12,
    pd_supply = 1.8, # V
    output_vs = 1, #  
    enable_cds = False,
    num_transistor = 3,
    # noise parameters
    dark_current_noise = 0.005, # mean dark current distribution (Poisson); unit: number of electrons
    enable_dcnu = True,
    enable_prnu = True,
    dcnu_std = 0.001, # standard deviation of mean dark current across the pixel array
    fd_gain = 1.0, # gain of the floating diffusion (FD)
    fd_noise = 0.005, # standard deviation of the electron count distribution (Gaussian) at FD
    fd_prnu_std = 0.001, # standard deviation FD gain distribution across the pixel array
    sf_gain = 1.0, # gain of the source follower (SF)
    sf_noise = 0.005, # standard deviation of the voltage distribution (Gaussian) at SF
    sf_prnu_std = 0.001 # standard deviation SF gain distribution across the pixel array
)
```

```python
ColumnAmplifier(
    # latency and performance parameters
    load_capacitance = 1e-12,  # [F]
    input_capacitance = 1e-12,  # [F]
    t_sample = 2e-6,  # [s]
    t_frame = 10e-3,  # [s]
    supply = 1.8,  # [V]
    gain = 1,
    # noise parameters
    noise = 0.005, # read noise of the amplifier (unit: voltage)
    enable_prnu = True,
    prnu_std = 0.001,
)
```
















