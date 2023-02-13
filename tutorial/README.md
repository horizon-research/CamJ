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
stride is `1x1x1` and the padding is `NONE` to make sure the output size still `32x32x1`.

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





























