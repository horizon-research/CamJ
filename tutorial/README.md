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
Overall system cycle count:  5761
[Cycle distribution] {Input: 2591, Conv1: 5039, Conv2: 2731, Abs: 573}
ADC total compute cycle:  1296 total compute energy: 777600 pJ
ConvUnit-1 total compute cycle:  1298 total compute energy: 5841 pJ
ConvUnit-2 total compute cycle:  146 total compute energy: 657 pJ
AbsUnit total compute cycle:  144 total compute energy: 72 pJ
LineBuffer total memory energy: 5182 pJ
FIFO-1 total memory energy: 5184 pJ
FIFO-2 total memory energy: 576 pJ
FIFO-3 total memory energy: 432 pJ
[End] Digitial Simulation is DONE!
```

## Code Walk-Through

In `tutorial_run.py`, `launch_simulation()` is the CamJ API that performs the energy simulation of a CIS. Follow how it's defined and what parameters it needs to understand how CamJ simulation works. Briefly, in order for CamJ to perform energy simulation, we need to specify three pieces of information: 1) the hardware description, 2) the algorithm description, and 3) algorithm to hardware mapping. They are `hw_dict`, `sw_stage_list`, and `mapping_dict` in the `launch_simulation` interface:

```python
launch_simulation(hw_dict, mapping_dict, sw_stage_list)
```

### Software Description

This CIS executes a simple software pipeline, which is described in `sw.py` and has four stages:

| Stage Name | Description                                   |
|------------|-----------------------------------------------|
| Input      | defines a 36x36x1 pixel input                 |
| Conv-1     | defines a 3x3x1 convolution with stride of 1  |
| Conv-2     | defines a 3x3x1 convolution with stride of 3  |
| Abs        | defines a element-wise absolute               |

In CamJ, any software pipeline starts with an input image, which is created by instaitiating a [`PixelInput`](https://github.com/horizon-research/CamJ/blob/main/camj/sim_core/sw_interface.py#L3) object in CamJ below, which says the pixel array captures a 36x36 image.
The naming convention in CamJ is that all the natively-supported hardware structures (compute and memory, analog and digital) are defined as UpperCamelCase-named classes.

```python
input_data = PixelInput((36, 36, 1), name="Input")
```

This raw pixel array is then sent through three sequential processing stages (using [`ProcessStage`](https://github.com/horizon-research/CamJ/blob/main/camj/sim_core/sw_interface.py#L31)). First one performs a simple 3x3 convolution with stride of 1, second one performs 3x3 convolutation with stride of 3, and the last performs an element-wise absolute operation.
We observe that image processing algorithms can be abstracted as stencil operations that operate on a local window of pixels at a time.
An element-wise stage is nothing more than a 1x1 stencil stage.

Therefore, users express only the input/output image dimensions (`input_size`, `output_size`) along with the
stencil window (`kernel_size`) and stride size (`stride`).
`num_kernels` is used to define when multiple kernels operates in one processing stages.
Given the regular computation and data access pattern of stencil operations, CamJ could accurately estimate the access
counts to different hardware structures for energy estimations.

For instance, the convolution stage is described as:

```python
# define a 3x3 convolution stage with stride of 1
conv1_stage = ProcessStage(
    name = "Conv1",
    input_size = [(36, 36, 1)], # (H, W, C)
    kernel_size = [(3, 3, 1)],  # (K_h, K_w, K_c)
    num_kernels = [1],
    stride = [(1, 1, 1)],       # (H, W, C)
    output_size = (36, 36, 1),  # with padding and stride of 1
    padding = [True]            # output size is the same as input
)

# define a 3x3 convolution stage with stride of 3
conv2_stage = ProcessStage(
    name = "Conv2",
    input_size = [(36, 36, 1)], # (H, W, C)
    kernel_size = [(3, 3, 1)],  # (K_h, K_w, K_c) 
    num_kernels = [1],
    stride = [(3, 3, 1)],       # (H, W, C)
    output_size = (12, 12, 1),  # with no padding and stride of 3
    padding = [False]           # output size becomes (12, 12, 1)
)

# define a 1x1 absolution stage
abs_stage = ProcessStage(
    name = "Abs",
    input_size = [(12, 12, 1)], # (H, W, C)
    kernel_size = [(1, 1, 1)],  # (K_h, K_w, K_c) 
    num_kernels = [1],
    stride = [(1, 1, 1)],       # (H, W, C)
    output_size = (12, 12, 1),  # same as input size
    padding = [False]
)
```

The `abs_stage` is similarly defined, but note that the `stride` is `[(1, 1, 1)]`.

We connect the software stages together:

```python
conv1_stage.set_input_stage(input_data)
conv2_stage.set_input_stage(conv1_stage)
abs_stage.set_input_stage(conv2_stage)
```

In the end, we need to put every stage into a single list used by `launch_simulation()`:

```python
sw_stage_list.append(input_data)
sw_stage_list.append(conv1_stage)
sw_stage_list.append(conv2_stage)
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

Our CIS needs four digital units, starting with an ADC created as an CamJ `ADC` object, and three compute units for two convolution operations and one absolute operation in the software pipeline.
The three compute units are instantiated as three CamJ [`ComputeUnit`](https://github.com/horizon-research/CamJ/blob/main/camj/sim_core/digital_compute.py#L191) objects.

```python
conv1_unit = ComputeUnit(
    name="ConvUnit-1",
    domain=ProcessDomain.DIGITAL,
    location=ProcessorLocation.SENSOR_LAYER,
    input_per_cycle = [(3, 1, 1)],          # take (3, 1, 1) of pixel per cycle
    output_per_cycle = (1, 1, 1),           # output (1, 1, 1) of pixel per cycle
    energy_per_cycle = 9*compute_op_power,  # the average energy per cycle
    num_of_stages = 3,                      # num of stages to output result, latency
    area = 30
)

conv2_unit = ComputeUnit(
    name="ConvUnit-2",
    domain=ProcessDomain.DIGITAL,
    location=ProcessorLocation.SENSOR_LAYER,
    input_per_cycle = [(3, 3, 1)],          # take (3, 3, 1) of pixel per cycle
    output_per_cycle = (1, 1, 1),           # output (1, 1, 1) of pixel per cycle
    energy_per_cycle = 9*compute_op_power,  # average energy per cycle
    num_of_stages = 3,                      # num of stage to output result. latency 
    area = 30
)

abs_unit = ComputeUnit(
    name="AbsUnit",
    domain=ProcessDomain.DIGITAL,
    location=ProcessorLocation.SENSOR_LAYER,
    input_per_cycle = [(1, 1, 1)],          # take (1, 1, 1) of pixel per cycle
    output_per_cycle = (1, 1, 1),           # output (1, 1, 1) of pixel per cycle
    energy_per_cycle = 1*compute_op_power,  # average energy per cycle
    num_of_stages = 1,                      # num of stage to output result. latency 
    area = 10
)
```

In `ComputeUnit`, we need to define the input and output per cycle of that unit. The input per cycle means the number of input elements needs to be read per cycle. The output per cycle is the number of output elements generated per cycle after fully pipelined.
We also need to specify a `num_of_stages` attribute, which indicates the number of stages in this compute unit.

For instance, `ConvUnit-1` has an input per cycle of `3x1x1` and the output per cycle is `1x1x1`. It has three stages. 
So the latency of `ConvUnit-1` is 3 cycles, but it generates (1, 1, 1) of element per cycle after it is fully pipelined.

In addition, CamJ also requires programmers to specify the per operation energy of each compute unit. 
The `location` attribute is used to define where this compute unit is.

#### Digital Memory Units

In this example, we will need one line buffer and three FIFOs as the digital memories. We create them by instantiating CamJ [`LineBuffer`](https://github.com/horizon-research/CamJ/blob/main/camj/sim_core/digital_memory.py#L71) and [`FIFO`](https://github.com/horizon-research/CamJ/blob/main/camj/sim_core/digital_memory.py#L166) objects.

The line buffer is used between pixel sensor readout and `ConvUnit-1`.
The first FIFO is used to save the result from `ConvUnit-1` and read by `ConvUnit-2`.
The second FIFO is used to save the result from `ConvUnit-2` and read by `AbsUnit`.
The last FIFO is used to save the result from `Absunit` and will eventually be transferred out of the CIS.

Here is the definition of these three memory structures:
```python
line_buffer = LineBuffer(
        name="LineBuffer",
        size = (3, 36),  # can 3x 32 number of pixels
        location = ProcessorLocation.COMPUTE_LAYER,
        write_energy_per_word = 3,  # 3pJ to write a word
        read_energy_per_word = 1,   # 1pJ to read a word
        write_word_length = 1,      # the word length or #pixel per write access
        read_word_length = 3,       # the word length or #pixel per read access
        write_unit = "ADC",
        read_unit = "ConvUnit-1"
    )

    fifo_buffer1 = FIFO(
        name="FIFO-1",
        size = 36*3,
        location = ProcessorLocation.COMPUTE_LAYER,
        write_energy_per_word = 3,  # 3pJ to write a word
        read_energy_per_word = 1,   # 1pJ to read a word
        write_word_length = 1,      # the word length or #pixel per write access
        read_word_length = 1,       # the word length or #pixel per read access
        write_unit = "ConvUnit-1",
        read_unit = "ConvUnit-2"
    )

    fifo_buffer2 = FIFO(
        name="FIFO-2",
        size = 12,
        location = ProcessorLocation.COMPUTE_LAYER,
        write_energy_per_word = 3,  # 3pJ to write a word
        read_energy_per_word = 1,   # 1pJ to read a word
        write_word_length = 1,      # the word length or #pixel per write access
        read_word_length = 1,       # the word length or #pixel per read access
        write_unit = "ConvUnit-2",
        read_unit = "AbsUnit"
    )

    fifo_buffer3 = FIFO(
        name="FIFO-3",
        size = 12*12,
        location = ProcessorLocation.COMPUTE_LAYER,
        write_energy_per_word = 3,  # 3pJ to write a word
        read_energy_per_word = 1,   # 1pJ to read a word
        write_word_length = 1,      # the word length or #pixel per write access
        read_word_length = 1,       # the word length or #pixel per read access 
        write_unit = "AbsUnit",
        read_unit = "AbsUnit"
    )
```

All four memory structures have different memory sizes as specified by `size` attribute.
The per-read and per-write energy consumption is 1 pJ and 3 pJ, respectively.

Also, we need to define the access unit for each line buffer. The compute unit that does not have the 
permission to access the memory structure is not able to access the memory structure.

Last, we define the connections between memory structures and compute units by using `set_input_buffer`
and `set_output_buffer`:

```python
adc.set_output_buffer(line_buffer)

conv1_unit.set_input_buffer(line_buffer)
conv1_unit.set_output_buffer(fifo_buffer1)

conv2_unit.set_input_buffer(fifo_buffer1)
conv2_unit.set_output_buffer(fifo_buffer2)

abs_unit.set_input_buffer(fifo_buffer2)
abs_unit.set_output_buffer(fifo_buffer3)
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
















