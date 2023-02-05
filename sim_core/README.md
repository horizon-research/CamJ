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

TODO

## Digital Configuration

`digital_compute.py` and `digital_memory.py` implements the building blocks for digital hardware 
simulation. In CamJ, we provide three compute building blocks:

- `ComputeUnit`: this is an interface for some basic compute hardware units, like some compute unit 
inside ISP.
- `SystolicArray`: this class simulates the behavior of a classic hardware design, systolic array.
- `NeuralProcessor`: this class is anothe example of DNN accelerator, it is a SIMD processor.






