
import numpy as np

class AnalogComponent(object):
	"""docstring for AnalogComponent"""
	def __init__(
		self,
		name : str,
		input_domain: list,
		output_domain: int,
		energy = None,
		num_input: list = [(1, 1)], 
		num_output: tuple = (1, 1)
	):
		super(AnalogComponent, self).__init__()
		self.name = name
		self.num_input = num_input
		self.num_output = num_output
		self.input_domain = input_domain
		self.output_domain = output_domain
		self.energy = energy
		self.components = []
		self.input_components = []
		self.output_components = []
	"""
		Key function to add component attributes to array
	"""
	def add_input_component(self, analog_component):
		self.input_components.append(analog_component)
		self.num_component[analog_component] = num_component

	def add_output_component(self, analog_component):
		self.output_components.append(analog_component)

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
		self.components = []
		self.input_domain = []
		self.output_domain = None
		self.input_arrays = []
		self.output_arrays = []
		self.source_components = []
		self.destination_components = []
		self.num_component = {}
	"""
		Key function to add components attributes to array
	"""
	def add_component(self, component: AnalogComponent, component_size: tuple):
		self.components.append(component)
		self.num_component[component] = component_size
	"""
		for each analog array, we need to set source component so that
		we know which component is the header to start simulation.
		Also, source components can allow us to know the input domain
		or analog array.
	"""
	def set_source_component(self, source_component: list):
		self.source_component = source_component
		for component in source_component:
			for domain in component.input_domain:
				self.input_domain.append(domain)

	"""
		for each analog array, define the destination component so that
		we can know the computation ends at the destination component.
		Also, we can know the output domain of this analog array.
	"""
	def set_destination_component(self, destination_component: list):
		self.destination_component = destination_component
		for component in destination_component:
			print(self.name, component.output_domain)
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

	def energy(self):
		total_compute_energy = 0
		for i in range(len(self.components)):
			component = self.components[i]
			num_component = self.calc_num(self.num_component[component])
			print(component, num_component)
			total_compute_energy += num_component * component.energy()

		return total_compute_energy

	def __str__(self):
		return self.name

	def __repr__(self):
		return self.name

		
