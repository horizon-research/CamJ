# IEEE VR Eye Tracking

This example shows how to describe paper [IEEE VR22](https://horizon-lab.org/pubs/vr22.pdf) using 
CamJ API.

## Described Pipeline

The following figure shows the software pipeline that this example describes:

![algo](https://user-images.githubusercontent.com/21286132/220165747-6cd26972-9ea9-4298-80eb-28ad070ec6d2.png)

We slightly modified the original pipeline so that it can be better described using CamJ API.

## File Descriptioins

`sw_pipeline.py` describes the software pipeline in the figure above. In particular, there are two 
functions in `sw_pipeline.py`. `sw_pipeline()` function describes the function, however, it 
corresponds to a design that puts every computation in digital domain. `sw_pipeline_w_analog()` shows
an example that deploys some computations (event map generation) in analog domain as the figure above
shows. 

`hw_config.py` shows the hardware descriptions for the pipeline above. Similarly, there are two
configuration functions. `hw_config()` shows the hardware configuration that puts all computations 
in digital domain. `hw_config_w_analog()` puts the event map generation to the analog domain. 

To be noticed, `hw_config_w_analog()` function also includes a customized analog component, 
`EventificationUnit`, which is not builtin analog component in CamJ. `EventificationUnit` is defined
in `customized_analog_component.py`. 

`mapping_file.py` defines the mapping between software stages and hardware components.
