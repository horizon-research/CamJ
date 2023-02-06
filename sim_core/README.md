# Sim-Core

This is the core library for power/energy estimation in CamJ framework.

## Structure of This Library

This library is organized into four major parts:
- *analog computing simulation*: `analog_infra.py`, `analog_lib.py` and `analog_utils.py` are 
modules or classes that are used for analog simulation.
- *digital computing simulation*: `digital_compute.py`, `digital_memory.py`, `sim_infra.py` 
and `sim_utils.py` are modules for digital simulation.
- *software interface*: `sw_interface.py` provides the software interface for users to provide
the software algorithms that they want to perform simulation.
- *harness code*: `launch.py`, `enum_const.py` and `flags.py` are harness codes or configuration flags
which can be modified if necessary.


## Software Configuration

In software interface, CamJ provides three main classes that allow users to describe most of image
processing algorithms, including conventional algorithms in image processing pipeline or DNN-based
algorithms that are running on GPU or customized hardware. 

These three classes are:
- *PixelInput*: this describes the input of the software algorithm. this class should be always at
the beginning at the software pipelines.
- *ProcessStage*: this class is used to describe the processing stensil operations in conventional
image processing pipeline or some operations like MaxPool or ReLU operations.
- *DNNProcessStage*: this class can describe major computation in DNN-based algorithms, such as
convolution, depthwise-convolution and fully-connected layer.

The following code describes an input with a shape of (640, 400, 1). In `PixelInput`, there is another attribute,
`functional_pipeline`, which is used for functional simulation. In this case, it is used to simulate
how to generate pixels. If you don't want to perform functional simulation, no need to specify this
attribute. To understand how to specify `functional_pipeline` attribute, please check out `functional_core` 
directory.
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
and stride size is (2, 2, 1). The computation order is a raster-scanning fashion. The reason that 
`input_size`, `kernel_size` and `stride` are lists of tuples is that CamJ allows one `ProcessStage` 
has multiple inputs. However, CamJ only allows one output per `ProcessStage`. In this example,
the output size is (320, 200, 1).

The following shows a convolution operation.
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
and stride size is 2. Operation types can be others such as `FC` and `DWConv2D`. 

After defining those classes, users also need to define the data dependency in the software pipeline.
For instance, the following code describes the `input_data` is the input of `resize_stage` and `resize_stage` 
is the input of `conv2d_stage`.
```
resize_stage.set_input_stage(input_data)
conv2d_stage.set_input_stage(resize_stage)

```
The above code just finishes describing a simple software pipeline using CamJ API.

## Analog Configuration

Analog configuration starts from describing a set of analog arrays. In each analog array, users also
need to define what analog components are inside. Here, we show an example of defining an analog array:

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
	energy = dummy_energy_func
)
```
Here, we define an analog array called `PixelArray`, the input/output of this pixel array is (640, 1, 1).
This shows each cycle, it can produce a row of 640 pixels. This `PixelArray` resides in `SENSOR_LAYER`. 
We also define an analog component called `Pixel`. The `Pixel` component has input domain and output
domain which allow CamJ framework to verify the correctness of the analog implementation. The `energy` 
attribute allows CamJ to compute the overall energy/power consumption.

```
pixel_array.add_component(pixel, (640, 400, 1))
pixel_array.set_source_component([pixel])
pixel_array.set_destination_component([pixel])
```
In addition to these two definations, we also need to define the structure and the connection of these 
analog array. Here, `add_component` function shows the pixel array has (640, 400, 1) of pixels. 
`set_source_component` and `set_destination_component` show the internal connections of pixel array. 
These two functions are used to determine the connection inside the analog array, in case there are 
multiple analog components inside one analog array.

## Digital Configuration

### Computation Building Blocks

Two files, `digital_compute.py` and `digital_memory.py`, implement the building blocks for 
digital hardware simulation. In CamJ, we provide four compute building blocks:

- `ADC`: 
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
	clock = XX, 	   # MHz
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







