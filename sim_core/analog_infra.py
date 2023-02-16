
import numpy as np
import copy

class AnalogComponent(object):
    """docstring for AnalogComponent"""
    def __init__(
        self,
        name : str,
        input_domain: list,
        output_domain: int,
        component_list = None,
        num_input: list = [(1, 1)], 
        num_output: tuple = (1, 1)
    ):
        super(AnalogComponent, self).__init__()
        self.name = name
        self.num_input = num_input
        self.num_output = num_output
        self.input_domain = input_domain
        self.output_domain = output_domain
        self.component_list = component_list
        self.components = []
        self.input_components = []
        self.output_components = []

    """
        Energy function compute the total energy of this component. 
        The total energy equals to the sum of (energy of each component) * (the number of such component)
    """
    def energy(self):
        total_energy = 0
        for i in range(len(self.component_list)):
            total_energy += self.component_list[i][0].energy() * self.component_list[i][1]

        return total_energy

    """
        The noise function performs the noise simulation based on the noise model of each component
        one-by-one.
    """
    def noise(self, input_signal_list):
        output_signal_list = copy.deepcopy(input_signal_list)

        for component in self.component_list:
            output_signal_list = component.noise(output_signal_list)

        return output_signal_list

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class AnalogArray(object):
    """docstring for AnalogArray"""
    def __init__(
        self,
        name : str,
        layer: int, 
        num_input: list, 
        num_output: tuple,
    ):
        super(AnalogArray, self).__init__()
        self.name = name
        self.num_input = num_input
        self.num_output = num_output
        self.layer = layer
        self.component = None
        self.input_domain = []
        self.output_domain = None
        self.input_arrays = []
        self.output_arrays = []
        self.source_component = []
        self.destination_component = []
        self.num_component = 0
    """
        Key function to add components attributes to array
    """
    def add_component(self, component: AnalogComponent, component_size: tuple):
        if self.component is not None:
            raise Exception("There are more than one component in analog array: '%s'." % self.name)

        self.component = component
        self.num_component = component_size

        self.set_source_component([component])
        self.set_destination_component([component])

    """
        for each analog array, we need to set source component so that
        we know which component is the header to start simulation.
        Also, source components can allow us to know the input domain
        or analog array.
    """
    def set_source_component(self, source_components: list):
        self.source_components = source_components
        for component in source_components:
            for domain in component.input_domain:
                self.input_domain.append(domain)

    """
        for each analog array, define the destination component so that
        we can know the computation ends at the destination component.
        Also, we can know the output domain of this analog array.
    """
    def set_destination_component(self, destination_components: list):
        self.destination_components = destination_components
        for component in destination_components:
            self.output_domain = component.output_domain

    def add_input_array(self, analog_array):
        self.input_arrays.append(analog_array)

    def add_output_array(self, analog_array):
        self.output_arrays.append(analog_array)
        
    def calc_num(self, num_component):
        cnt = 1
        for i in num_component:
            cnt *= i

        return cnt

    def noise(self, input_signal_list):
        output_signal_list = copy.deepcopy(input_signal_list)

        for component, _ in self.component.component_list:
            output_signal_list = component.noise(output_signal_list)

        return output_signal_list

    def energy(self):
        num_component = self.calc_num(self.num_component)
        total_compute_energy = num_component * self.component.energy()

        return total_compute_energy

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

        
