# Sim-Core

This is the core library for power/energy estimation in CamJ framework.

## Structure of This Library

This library is organized into four major parts:
- *analog computing simulation*: `analog_infra.py`, `analog_lib.py`, `analog_perf_lib.py` and 
`analog_utils.py` are modules or classes that are used for analog simulation.
- *digital computing simulation*: `digital_compute.py`, `digital_memory.py`, `sim_infra.py` 
and `sim_utils.py` are modules for digital simulation.
- *software interface*: `sw_interface.py` provides the software interface for users to provide
the software algorithms that they want to perform simulation. `sw_utils.py` contains utility code
for software pipeline.
- *harness code*: `launch.py`, `enum_const.py` and `flags.py` are harness codes and configuration flags
which can be modified if necessary.


## Software Configuration

In software interface, CamJ provides three main classes that allow users to describe most of image
processing algorithms, including conventional algorithms in image processing pipeline or DNN-based
algorithms that are running on GPU or customized hardware. 

CamJ provides three classes for users to describe their algorithms:
- `PixelInput`: this describes the input of the software algorithm. this class should be always at
the beginning at the software pipelines.
- `ProcessStage`: this class is used to describe the processing stensil operations in conventional
image processing pipeline or some operations like MaxPool or ReLU operations.
- `DNNProcessStage`: this class can describe major computation in DNN-based algorithms. Currently,
CamJ supports 2D convolution, 2D depthwise-convolution and fully-connected layer.

The following code shows an example to describe an input with a shape of (640, 400, 1). 
```
input_data = PixelInput(
    (640, 400, 1), 
    name="Input",
)
```
To define a resize function, you can use `ProcessStage` class.
```
resize_stage = ProcessStage(
    name = "Resize",
    input_size = [(640, 400, 1)],
    kernel_size = [(2, 2, 1)],
    stride = [(2, 2, 1)],
    output_size = (320, 200, 1),
    padding =[Padding.NONE]
)
```
This instance describes a resize operation. The input size is (640, 400, 1). The kernel size is (2, 2, 1)
and stride size is (2, 2, 1). The computation order is a raster-scanning fashion. As you can see, 
CamJ does not need users to specify the exact computation just dataflow and input/output dimensions.
This largely simplifies the definition work. In the definition, `input_size`, `kernel_size` and 
`stride` are lists of tuples. This is beccause that CamJ allows one `ProcessStage` has multiple inputs. 
However, CamJ only allows one output per `ProcessStage`. In this example, the output size is (320, 200, 1).

The following shows a DNN operations, a convolution operation.
```
conv2d_stage = DNNProcessStage(
    name = "Conv2D",
    op_type = "Conv2D",
    ifmap_size = [320, 200, 1],
    kernel_size = [3, 3, 1, 32],
    stride = 2
)
```
This example shows a convolution layer with input size of (320, 200, 1), the kernel size is (3, 3, 1, 32) 
(the kernel size is (3, 3, 1) with 32 number of kernels). Stride size is 2. Here, the operation type 
is `Conv2D` (2D Convolution). Operation types can be others such as `FC` and `DWConv2D`. 

After defining those classes, users also need to define the data dependency in the software pipeline.
For instance, the following code describes the `input_data` is the input of `resize_stage` and 
`resize_stage` is the input of `conv2d_stage`.
```
resize_stage.set_input_stage(input_data)
conv2d_stage.set_input_stage(resize_stage)

```
After describing the data dependencies, you just finished describing a simple software pipeline 
using CamJ API!

## Analog Configuration

CamJ describes analog structures in a two-level fashion. At the uppper level, CamJ asks users to 
describe a set of analog arrays. Then, at the lower level, users are asked to define what analog 
components are inside each analog array. Here, we show an example of defining an analog array:

```
pixel_array = AnalogArray(
    name = "PixelArray",
    layer = ProcessorLocation.SENSOR_LAYER,
    num_input = [(640, 1, 1)],
    num_output = (640, 1, 1)
)
pixel = AnalogComponent(
    name = "Pixel",
    input_domain =[ProcessDomain.OPTICAL],
    output_domain = ProcessDomain.TIME,
    component_list = ...
)
```
Here, we define an analog array called `PixelArray`, the input/output throughputs of this pixel array
are both (640, 1, 1). This shows each cycle, it can generate a row of 640 pixels. `SENSOR_LAYER` 
attribute shows that this `PixelArray` resides in sensor layer. In addition to `PixelArray`, we also
need to define an analog component called `Pixel`. The `Pixel` component has input domain and output
domain which allow CamJ framework to verify the correctness of the analog implementation. `component_list` 
attribute defines the implementation of this analog component. This information allows CamJ to 
estimate the overall energy/power consumption and perform functional simulation. [`analog_libs.py`](https://github.com/horizon-research/in-sensor-simulator/tree/main/sim_core/analog_libs.py) 
contains the analog compoenents that CamJ supports for energy/functional simulation.

```
pixel_array.add_component(pixel, (640, 400, 1))
```

In addition to these two definitions, we also need to define the structure and the connection of this 
pixel array. Here, `add_component` function shows the pixel array has (640, 400, 1) of pixels. In 
current CamJ implementation, each `AnalogArray` allows users to add multiple `AnalogComponent`. This
allows one analog array has two different analog component with different shapes. For instance, one
pixel array can have have (640, 400, 1) number of pixels and (640, 1, 1) number of column amplifiers.
Additionally, `AnalogComponent` (considered as a super-component) can add multiple analog basic 
components with the same structure shape.

## Digital Configuration

### Computation Building Blocks

Two files, `digital_compute.py` and `digital_memory.py`, implement the building blocks for 
digital hardware simulation. In CamJ, we provide four compute building blocks:

- `ADC`: the interface between analog and digital simulation.
- `ComputeUnit`: this is an interface for some basic compute hardware units, like some compute unit 
inside ISP.
- `SystolicArray`: this class simulates the behavior of a classic hardware design, systolic array.
- `NeuralProcessor`: this class is anothe example of DNN accelerator, it is a SIMD processor.

Next, we show how to use these classes.
```
adc = ADC(
    name = "ADC",
    output_throughput = (640, 1, 1),
    location = ProcessorLocation.SENSOR_LAYER,
)
```
Analog-to-digital convertor (ADC) is the interface between analog and digital world. In CamJ, to
bridge these two parts, users need to define a ADC instance. Here, ADC has two attributes. 
`output_throughput` shows in which order ADC outputs pixels. In this case, the order is (640, 1, 1),
this is a typical order as a rolling shutter. `location` shows where ADC resides.

```
resize_unit = ComputeUnit(
    name="ResizeUnit",
    domain=ProcessDomain.DIGITAL,
    location=ProcessorLocation.SENSOR_LAYER,
    input_throughput = [(32, 2, 1)],
    output_throughput = (16, 1, 1), 
    clock = XX, # MHz
    energy = XX,
    area = XX,
    initial_delay = 0,
    delay = 3,
)
```
This example shows how to define a hardware unit that performs 2x2 resize. `domain` attribute defines
which domain this operation performs in. `location` defines the location that this hardware unit resides.
Two important parameters, `input_throughput` and `output_throughput`, define that to output a size of 
(16, 1, 1) output, this resize unit takes (32, 2, 1) of data from input. The parameter `initial_delay`
describes the initial number of cycle that this resize unit takes to let resize unit fully pipelined.
`delay` parameter shows after `initial_delay` cycles, the number of cycles takes to output 
the next batch (16, 1, 1) output. These parameters is useful that allows CamJ simulator to understand 
the actual hardware behavior.

```
dnn_acc = SystolicArray(
    name="InSensorSystolicArray",
    domain=ProcessDomain.DIGITAL,
    location=ProcessorLocation.COMPUTE_LAYER,
    size_dimension=(16, 16),
    clock=XX,
    energy=XX,
    area=XX
)
```
The code above shows an example of how to use `SystolicArray` class. Here, we define a systolic array 
of size 16x16. Because the computation pattern of a systolic array is well defined, no extra parameter 
is needed to define the computation pattern.

### Memory Building Blocks

CamJ provides three main memory building blocks:
- `DoubleBuffer`: a generic double buffer structure. It uses to hide the memory latency, while the 
loading buffer is fetching data, the working buffer is used for computation.
- `LineBuffer`: it allows multiple reads per cycle and only one write to its buffer.
- `FIFO`: this is a special example of `LineBuffer`, it only allows one read to the next stage and 
one writes from the previous stage.

```
fifo_buffer = FIFO(
    name="FIFO",
    hw_impl = "sram",
    count = 1280,
    clock = XX,        # MHz
    write_energy = XX, #pJ
    read_energy = XX,  #pJ
    location = ProcessorLocation.COMPUTE_LAYER,
    duplication = 100,
    write_unit = "ADC",
    read_unit = "ResizeUnit"
)

```
This code shows how to define a FIFO using CamJ API. `hw_impl` shows the actual implementation of FIFO.
`count` and `duplication` shows the size of FIFO and the word size of each word. `write_unit` and `read_unit` 
show which  hardware unit can access this FIFO.

For other memory instance examples, please check `simple_example` and `ieee_vr22` directory for more 
details.






