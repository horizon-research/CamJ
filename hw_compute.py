import numpy as np


class ADC(object):
    """docstring for ADC"""

    def __init__(
            self,
            name: str,
            type: int,
            pixel_adc_ratio: tuple,
            output_throughput: tuple,
            location
    ):
        super(ADC, self).__init__()
        self.name = "ADC"
        self.type = type
        self.pixel_adc_ratio = pixel_adc_ratio
        self.output_throughput = output_throughput
        self.location = location
        self.input_buffer = None
        self.input_hw_units = {}
        self.output_buffer_size = {}
        self.output_index_list = {}

        self.delay = 1
        self.elapse_cycle = -1

    def set_input_buffer(self, input_buffer):
        self.input_buffer = input_buffer

    def set_output_buffer(self, output_buffer):
        self.output_buffer = output_buffer

    def init_output_buffer_index(self, sw_stage, buffer_size):
        self.output_buffer_size[sw_stage] = buffer_size
        self.output_index_list[sw_stage] = []
        for i in buffer_size:
            self.output_index_list[sw_stage].append(0)

    def get_output_buffer_index(self, sw_stage):
        return self.output_index_list[sw_stage]

    def set_output_buffer_index(self, sw_stage, output_buffer_index):
        self.output_index_list[sw_stage] = output_buffer_index

    # initialize the cycle number that needs to be elapsed before writing the output
    def init_elapse_cycle(self):
        self.elapse_cycle = self.delay

    # process one cycle
    def process_one_cycle(self):
        self.elapse_cycle -= 1

    # check if the compute is finished, if finished, reset the elapse cycle number
    def finish_computation(self):
        if self.elapse_cycle == 0:
            self.elapse_cycle = -1
            return True
        else:
            return False

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


'''
 	This is the generic Compute Unit interface for both digital and analog.
 	It can be used directly or extended to a derived class.
	Four attributes are important to define the behavior of the compute unit.
		1. input throughput: it is a list of tuples, each tuple defines the input throughput for one
			perticular source HW unit (producer).
		2. output throughput: it is a tuple, to define the output throughput shape for each compute.
		3. delay: assume the stage is fully pipelined, in that case, how long it takes to obtain one
			batch of output result.
		4. initial delay: it is the initial delay before this stage is fully pipelined.
'''


class ComputeUnit(object):
    """docstring for ComputeUnit"""

    def __init__(
            self,
            name: str,
            domain: int,  # whether is digital or analog
            location: int,  # location of this unit
            input_throughput: list,  # This is the input requirement in order to perform compute on this unit
            output_throughput: list,  # the number of element can be written out once one batch of compute is finished.
            clock: int,  # clock frequency
            energy: float,
            area: float,
            initial_delay: int,  # # of clock cycles to propogate data before starting the first computation
            delay: int  # # of clock cycles to finish one computation process when fully pipelined.
    ):
        super(ComputeUnit, self).__init__()
        # assign variables
        self.name = name
        self.domain = domain
        self.location = location

        self.input_throughput = input_throughput
        self.output_throughput = output_throughput

        self.clock_frequency = clock
        self.energy = energy
        self.area = area
        # setup the delay for the entire compute
        self.initial_delay = initial_delay
        self.delay = delay
        self.elapse_cycle = -1

        self.input_hw_units = {}
        self.input_index_list = {}
        self.output_buffer_size = {}
        self.output_index_list = {}

    # needs to set the input and output buffer
    def set_input_buffer(self, input_buffer):
        self.input_buffer = input_buffer

    def set_output_buffer(self, output_buffer):
        self.output_buffer = output_buffer

    # set the input hw units, the final input hw units is a list,
    # we assume multiple hw units as input
    def set_input_hw_unit(self, sw_stage, hw_unit):
        if sw_stage not in self.input_hw_units:
            self.input_hw_units[sw_stage] = [hw_unit]
        else:
            self.input_hw_units[sw_stage].append(hw_unit)

    # initialize input buffer index, so that we know where to the next data
    # the buffer index will be indexed using (source hw unit, sw stage)
    def init_input_buffer_index(self, src_hw_unit, sw_stage, buffer_size):
        self.input_index_list[src_hw_unit, sw_stage] = []
        for i in buffer_size:
            self.input_index_list[src_hw_unit, sw_stage].append(0)

    # get/set input buffer index
    def get_input_buffer_index(self, src_hw_unit, sw_stage):
        return self.input_index_list[src_hw_unit, sw_stage]

    def set_input_buffer_index(self, src_hw_unit, sw_stage, input_buffer_index):
        self.input_index_list[src_hw_unit, sw_stage] = input_buffer_index

    # initial output buffer index, here only sw stage is used as index,
    # because we consider only one output buffer
    def init_output_buffer_index(self, sw_stage, buffer_size):
        self.output_buffer_size[sw_stage] = buffer_size
        self.output_index_list[sw_stage] = []
        for i in buffer_size:
            self.output_index_list[sw_stage].append(0)

    # get/set output buffer index
    def get_output_buffer_index(self, sw_stage):
        return self.output_index_list[sw_stage]

    def set_output_buffer_index(self, sw_stage, output_buffer_index):
        self.output_index_list[sw_stage] = output_buffer_index

    # initialize the cycle number that needs to be elapsed before writing the output
    def init_elapse_cycle(self):
        self.elapse_cycle = self.delay

    # process one cycle
    def process_one_cycle(self):
        self.elapse_cycle -= 1

    # check if the compute is finished, if finished, reset the elapse cycle number
    def finish_computation(self):
        if self.elapse_cycle == 0:
            self.elapse_cycle = -1
            return True
        else:
            return False

    def compute_energy(self):
        return self.energy

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class SystolicArray(object):
    """docstring for SystolicArray"""

    def __init__(
            self,
            name,
            domain,
            location,
            size_dimension,
            clock,
            energy,
            area
    ):
        super(SystolicArray, self).__init__()
        self.name = name
        self.domain = domain
        self.location = location
        self.size_dimension = size_dimension
        self.clock_frequency = clock
        self.energy = energy
        self.area = area
        self.input_hw_units = {}
        self.input_index_list = {}
        self.input_throughput = [
            (size_dimension[0], 1, 1)
        ]
        self.output_buffer_size = {}
        self.output_index_list = {}

        self.delay = 10
        self.elapse_cycle = -1

    # needs to set the input and output buffer
    def set_input_buffer(self, input_buffer):
        self.input_buffer = input_buffer

    def set_output_buffer(self, output_buffer):
        self.output_buffer = output_buffer

    # set the input hw units, the final input hw units is a list,
    # we assume multiple hw units as input
    def set_input_hw_unit(self, sw_stage, hw_unit):
        if sw_stage not in self.input_hw_units:
            self.input_hw_units[sw_stage] = [hw_unit]
        else:
            self.input_hw_units[sw_stage].append(hw_unit)

    # initialize input buffer index, so that we know where to the next data
    # the buffer index will be indexed using (source hw unit, sw stage)
    def init_input_buffer_index(self, src_hw_unit, sw_stage, buffer_size):
        self.input_index_list[src_hw_unit, sw_stage] = []
        for i in buffer_size:
            self.input_index_list[src_hw_unit, sw_stage].append(0)

    # get/set input buffer index
    def get_input_buffer_index(self, src_hw_unit, sw_stage):
        return self.input_index_list[src_hw_unit, sw_stage]

    def set_input_buffer_index(self, src_hw_unit, sw_stage, input_buffer_index):
        self.input_index_list[src_hw_unit, sw_stage] = input_buffer_index

    # initial output buffer index, here only sw stage is used as index,
    # because we consider only one output buffer
    def init_output_buffer_index(self, sw_stage, buffer_size):

        self.output_throughput = np.ones_like(buffer_size)
        self.output_throughput[0] = self.size_dimension[0]

        self.output_buffer_size[sw_stage] = buffer_size

        self.output_index_list[sw_stage] = []
        for i in buffer_size:
            self.output_index_list[sw_stage].append(0)

    # get/set output buffer index
    def get_output_buffer_index(self, sw_stage):
        return self.output_index_list[sw_stage]

    def set_output_buffer_index(self, sw_stage, output_buffer_index):
        self.output_index_list[sw_stage] = output_buffer_index

    # initialize the cycle number that needs to be elapsed before writing the output
    def init_elapse_cycle(self):
        self.elapse_cycle = self.delay

    # process one cycle
    def process_one_cycle(self):
        self.elapse_cycle -= 1
        print(self.name, "just compute 1 cycle, %d cycles left" % self.elapse_cycle)

    # check if the compute is finished, if finished, reset the elapse cycle number
    def finish_computation(self):
        if self.elapse_cycle == 0:
            self.elapse_cycle = -1
            return True
        else:
            return False

    def compute_energy(self):
        return self.energy

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name
