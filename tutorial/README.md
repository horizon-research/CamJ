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
| functional_pipeline.py| the functional simulation configuration       | 

Next, we introduce each configuration file piece by piece,

## Software Configuration

In this example, we define a simple image pipeline, but this example can touch most of CamJ API. The
list below shows the stages inside this software pipeline.

| Stage Name | Description                                   |
|------------|-----------------------------------------------|
| Input      | defines a 32x32x1 pixel input                 |
| Conv       | defines a 3x3x1 convolution with stride of 1  |
| Abs        | defines a element-wise absolute difference    |

