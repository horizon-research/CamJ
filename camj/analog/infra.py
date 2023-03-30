import numpy as np
import copy

from camj.analog.component import Voltage2VoltageConv, Time2VoltageConv, BinaryWeightConv,\
                                PassiveBinning, ActiveAverage, ActiveBinning, MaxPool

class AnalogComponent(object):
    """Analog Component

    This is the low-level interface to define an analog component. This class serves as a container
    that consists of mulitple analog components from ``analog.component`` module.

    Args:
        name (str): the name of this analog component.
        input_domain (list): a list contains input domains. Each input domain defines the domain of
            each input signal. This ``input_domain`` list should match ``num_input``. Domains are
            defined in ``general.enum.ProcessDomain``.
        output_domain (enum): the domain of the output signal of this analog component. Domains are
            defined in ``general.enum.ProcessDomain``.
        component_list (list): a list of analog components that construct this ``AnalogComponent`` instance.
        num_input (list): a list of tuple, each tuple represents an input shape. Each input shape
            represents the number of input signals needed to obtain the output signal (``num_output``)
            per cycle. Each input shape is a 3D tuple in (H, W, C) format.
        num_output (tuple): the number of output signals per cycle in this output shape. 

    Examples:
        To create a mega-pixel component with 2x2 binning capability.

        >>> AnalogComponent(
            name = "BiningPixel",
            input_domain =[ProcessDomain.OPTICAL],
            output_domain = ProcessDomain.VOLTAGE,
            component_list = [(ActivePixelSensor(...), 4)],
            num_input = [],
            num_output = (1, 1, 1)
        )

        Here, ``ProcessDomain.OPTICAL`` shows pixel takes photons as input and converts to 
        ``ProcessDomain.VOLTAGE`` as shown in ``output_domain``. ``component_list`` shows
        how this analog component is implemented. In this case, it is ``ActivePixelSensor``.
        Each Pixel needs 4 ``ActivePixelSensor`` to achieve 2x2 binning.
    """
    def __init__(
        self,
        name : str,
        input_domain: list,
        output_domain: int,
        component_list = None,
        num_input: list = [(1, 1, 1)],  # (H, W, C)
        num_output: tuple = (1, 1, 1),  # (H, W, C)
    ):
        super(AnalogComponent, self).__init__()

        assert len(num_output) == 3, "'%s' num_output needs to be a size of 3." % name

        self.name = name
        # covert (h, w, c) to internal representation (x, y, z)
        self.num_input = _convert_hwc_to_xyz(name, num_input)
        self.num_output = (
            num_output[1],
            num_output[0],
            num_output[2]
        ) # covert (h, w, c) to internal representation (x, y, z)
        self.input_domain = input_domain
        self.output_domain = output_domain
        self.component_list = component_list

    """
        Energy function compute the total energy of this component. 
        The total energy equals to the sum of 
        (energy of each component) * (the number of such component)
    """
    def energy(self):
        """Calculate the energy consumption of this analog compoenent.

        This function calculates the overall energy consumption for this analog component per cycle.
        The overall energy equals to the energy consumption of each component in ``component_list``
        times the count of each component.

        Returns:
            Energy (float) in pJ.
        """
        total_energy = 0
        for i in range(len(self.component_list)):
            total_energy += self.component_list[i][0].energy() * self.component_list[i][1]

        return total_energy

    
    def noise(self, input_signal_list):
        """Noise Simulation

        The noise function performs the functional/noise simulation based on the functional model
        of each component in ``component_list``. The input signal will pass through each component's
        functional model one-by-one.

        Args:
            input_signal_list (list): a list of input signals in a form of numpy array.

        Returns:
            Simulated output signal after each analog component (dict)
        """
        output_signal_list = copy.deepcopy(input_signal_list)

        for component in self.component_list:
            output_signal_list = component.noise(output_signal_list)

        return output_signal_list

    def _configure_operation(self, sw_stage):
        """COnfigure analog component

        This function configure the analog component based on the software stage information.
        
        """
        for comp, _ in self.component_list:
            if isinstance(comp, Voltage2VoltageConv) or isinstance(comp, Time2VoltageConv) or isinstance(comp, BinaryWeightConv):
                comp._set_conv_config(
                    kernel_size = sw_stage.kernel_size,
                    num_kernels = sw_stage.num_kernels,
                    stride = sw_stage.stride
                )
            elif isinstance(comp, PassiveBinning) or isinstance(comp, ActiveBinning) \
                or isinstance(comp, ActiveAverage) or isinstance(comp, MaxPool):
                comp._set_binning_config(
                    kernel_size = sw_stage.kernel_size
                )

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class AnalogArray(object):
    """AnalogArray

    The High-level interface to define analog structures. In ``CamJ``, each analog array is
    defined as a 2D structure. In this structure, it contains multiple ``AnalogComponent`` s.
    Additionally, each ``AnalogArray`` has a regular input/output rate.

    Args:
        name (str): the name of this analog array.
        layer (int): the location of this analog array. Please see ``general.enum.ProcessorLocation``.
        num_input (list): a list of input 3D shapes in (H, W, C) format. Each input defines the number
            of input signals needed per cycle in order to obtain the output define in ``num_output``.

        num_output (tuple): output signals per cycle in 3D shape (H, W, C).
    """
    def __init__(
        self,
        name : str,
        layer: int, 
        num_input: list, 
        num_output: tuple,
    ):
        super(AnalogArray, self).__init__()

        assert len(num_output) == 3, "'%s' num_output needs to be a size of 3." % name

        self.name = name
        # covert (h, w, c) to internal representation (x, y, z)
        if num_input is not None:
            self.num_input = _convert_hwc_to_xyz(name, num_input)
        else:
            self.num_input = None
        self.num_output = (
            num_output[1],
            num_output[0],
            num_output[2]
        ) # covert (h, w, c) to internal representation (x, y, z)
        self.layer = layer
        self.components = []
        self.input_domain = []
        self.output_domain = None
        self.input_arrays = []
        self.output_arrays = []
        self.source_component = []
        self.destination_component = []
        self.num_component = {}

    def add_component(self, component: AnalogComponent, component_size: tuple):
        """Add components to its component list

        This function adds the analog components that construct this analog array.
        Multiple calls of this function will add multiple components to this analog array.

        Args:
            component (AnalogComponent): the analog component that constructs this analog array.
            component_size (tuple): the number of compoenent needs for this analog array.
                ``Component_size`` needs in a 3D shape (H, W, C).

        Returns:
            None
        """

        assert len(component_size) == 3, "'%s' component size needs to be a size of 3." % self.name

        self.components.append(component)
        self.num_component[component] = component_size

        # if it is the first element in the component list, set this element as the source
        # so that we can check the input/output domain consistency across different analog array.
        if len(self.components) == 1:
            self._set_source_component([component])
        # always the last added component as the destination component
        self._set_destination_component([component])

    def add_input_array(self, analog_array):
        """Add producer of this analog array

        Define the producer of this analog array. If multiple producers are needed, call
        this function multiple times.

        Args:
            analog_array (AnalogArray): the producer of this analog array.

        Returns:
            None
        """
        self.input_arrays.append(analog_array)

    def add_output_array(self, analog_array):
        """Add consumer of this analog array

        Define the consumer of this analog array. If multiple consumers are needed, call
        this function multiple times.

        Args:
            analog_array (AnalogArray): the consumer of this analog array.

        Returns:
            None
        """
        self.output_arrays.append(analog_array)

    def energy(self):
        """Energy consumption

        Calculate the energy needed to generate the given output shape.

        Return:
            Energy (float): energy consumption in J.
        """
        total_compute_energy = 0
        for component in self.components:
            output_ratio = self._calc_output_ratio(
                self.num_output, 
                component.num_output
            )
            total_compute_energy += component.energy() * output_ratio

        return total_compute_energy

    def noise(self, input_signal_list: list):
        """Function and Noise Simulation

        This function will iterate each component in the component list and perform
        functional and noise simulation for each component.

        Args:
            input_signal_list (list): a list of input signal to this analog array.

        Returns:
            Simulation result (list): the signal simulation result after each analog component.
            Each item in this list is a tuple in (component_name, output_signal_list) format.
        """
        output_signal_list = copy.deepcopy(input_signal_list)
        simulation_res = []
        # iterate components in order and model noise suquentially
        for component in self.components:
            # also iterate the sub-components
            for subcomponent, _ in component.component_list:
                subcomponent_name, output_signal_list = subcomponent.noise(output_signal_list)
                simulation_res.append(
                    (
                        subcomponent_name,
                        output_signal_list
                    )
                )

        return simulation_res

    def _set_source_component(self, source_components: list):
        """Set Source Component

        For each analog array, we need to set source component so that
        we know which component is the header to start simulation.
        Also, source components can allow us to know the input domain
        or analog array.
        """
        self.source_components = source_components
        for component in source_components:
            for domain in component.input_domain:
                self.input_domain.append(domain)

    def _set_destination_component(self, destination_components: list):
        """Set Destination Component

        For each analog array, define the destination component so that
        we can know the computation ends at the destination component.
        Also, we can know the output domain of this analog array.
        """
        self.destination_components = destination_components
        self.output_domain = []
        for component in destination_components:
            self.output_domain = component.output_domain

    def _configure_operation(self, sw_stage):
        for component in self.components:
            component._configure_operation(sw_stage)

    def _calc_output_ratio(self, array_ouput, comp_output):
        array_throughput = 1
        comp_throughput = 1
        for i in array_ouput:
            array_throughput *= i

        for i in comp_output:
            comp_throughput *= i

        return array_throughput / comp_throughput

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


# this function is used to convert size (H, W, C) to (X, Y, Z)
# it is hard to change the internal simulation code, this is an easy fix!
def _convert_hwc_to_xyz(name, size_list):
    new_size_list = []
    for size in size_list:
        assert len(size) == 3, "In %s, defined size needs to a size of 3!" % name
        new_size_list.append((size[1], size[0], size[2]))

    return new_size_list     
