
import numpy as np


class AnalogComponent(object):
	"""docstring for AnalogComponent"""
	def __init__(
		self,
		name: str,
		input_domain: list,
		output_domain: int,
		energy,
	):
		self.name = name
		self.input_domain = input_domain
		self.output_domain = output_domain
		self.energy_func = energy
		self.input_component = []
		self.output_component = []

	def energy(self):
		return self.energy_func()

	def add_input_component(self, component):
		self.input_component.append(component)

	def add_output_component(self, component):
		self.output_component.append(component)

	def __str__(self):
		return self.name

	def __repr__(self):
		return self.name


class AnalogUnit(object):
	"""docstring for AnalogUnit"""
	def __init__(
		self,
		name : str,
		input_domain: list,
		output_domain: int,
		energy = None,
		num_input: list = [(1, 1)], 
		num_output: tuple = (1, 1)
	):
		super(AnalogUnit, self).__init__()
		self.name = name
		self.num_input = num_input
		self.num_output = num_output
		self.input_domain = input_domain
		self.output_domain = output_domain
		self.energy = energy
		self.num_component = {}
		self.components = []
		self.input_units = []
		self.output_units = []
		self.source_component = []
		self.destination_component = []
	"""
		Key function to add component attributes to array
	"""
	def add_component(self, component: AnalogComponent, component_size: tuple):
		self.components.append(component)
		self.num_component[component] = component_size

	def set_source_component(self, source_component: list):
		self.source_component = source_component

	def set_destination_component(self, destination_component: list):
		self.destination_component = destination_component

	def add_input_unit(self, analog_unit):
		self.input_units.append(analog_unit)
		self.num_unit[analog_unit] = num_unit

	def add_output_unit(self, analog_unit):
		self.output_units.append(analog_unit)
		
	def calc_num(self, num_component):
		cnt = 1
		for e in num_component:
			cnt *= e

		return cnt

	def sum_energy(self):
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
		self.units = []
		self.input_domain = []
		self.output_domain = None
		self.input_arrays = []
		self.output_arrays = []
		self.source_units = []
		self.destination_units = []
		self.num_unit = {}
	"""
		Key function to add units attributes to array
	"""
	def add_unit(self, unit: AnalogUnit, unit_size: tuple):
		self.units.append(unit)
		self.num_unit[unit] = unit_size
	"""
		for each analog array, we need to set source unit so that
		we know which unit is the header to start simulation.
		Also, source units can allow us to know the input domain
		or analog array.
	"""
	def set_source_unit(self, source_unit: list):
		self.source_unit = source_unit
		for unit in source_unit:
			for domain in unit.input_domain:
				self.input_domain.append(domain)

	"""
		for each analog array, define the destination unit so that
		we can know the computation ends at the destination unit.
		Also, we can know the output domain of this analog array.
	"""
	def set_destination_unit(self, destination_unit: list):
		self.destination_unit = destination_unit
		for unit in destination_unit:
			print(self.name, unit.output_domain)
			self.output_domain = unit.output_domain

	def add_input_array(self, analog_array):
		self.input_arrays.append(analog_array)

	def add_output_array(self, analog_array):
		self.output_arrays.append(analog_array)
		
	def calc_num(self, num_unit):
		cnt = 1
		for i in num_unit:
			cnt *= i

		return cnt

	def energy(self):
		total_compute_energy = 0
		for i in range(len(self.units)):
			unit = self.units[i]
			num_unit = self.calc_num(self.num_unit[unit])
			print(unit, num_unit)
			if unit.energy is None:
				total_compute_energy += num_unit * unit.sum_energy()
			else:
				total_compute_energy += num_unit * unit.energy()

		return total_compute_energy

	def __str__(self):
		return self.name

	def __repr__(self):
		return self.name

		
