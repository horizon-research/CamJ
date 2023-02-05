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

The following code describes an input with a shape of (640, 400, 1). There is another attribute,
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

## Analog Configuration

TODO

## Digital Configuration




