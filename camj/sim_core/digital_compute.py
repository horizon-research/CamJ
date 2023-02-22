
import numpy as np
from camj.sim_core.flags import *

R_W_ENERGY = 4.1 # pJ


'''
    TODO: For now, just consider ADC as a compute unit, can be modified it later.
'''
class ADC(object):
    """docstring for ADC"""
    def __init__(
        self,
        name: str, 
        output_throughput: tuple,
        location,
        power = 600
    ):
        super(ADC, self).__init__()
        self.name = "ADC"
        self.input_throughput = None
        self.output_throughput = output_throughput
        self.location = location
        self.power = 600
        self.input_buffer = None
        self.input_hw_units = {}
        self.output_buffer_size = {}
        self.output_index_list = {}
        # parameters for computing stage
        self.delay = 1
        self.initial_delay = 0
        self.elapse_cycle = -1
        # parameters for reading stage
        self.read_cnt = -1 # num of input already being read for one compute
        self.total_read = -1 # total num of reads
        # parameters for writing stage
        self.write_cnt = -1 # num of output already being written for one compute
        self.total_write = -1 # total num of write

        # performance counter
        self.sys_all_compute_cycle = 0
        self.sys_all_write_cnt = 0
        self.sys_all_read_cnt = 0

    def set_input_buffer(self, input_buffer):
        self.input_buffer = input_buffer

    def set_output_buffer(self, output_buffer):
        self.output_buffer = output_buffer

    def init_output_buffer_index(self, sw_stage, buffer_size):
        self.output_buffer_size[sw_stage] = buffer_size
        self.output_index_list[sw_stage] = []
        for i in buffer_size:
            self.output_index_list[sw_stage].append(0)

    def get_output_buffer_size(self, sw_stage):
        return self.output_buffer_size[sw_stage]

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
        self.sys_all_compute_cycle += 1

    # dummy function
    def start_init_delay(self):
        pass

    # check if the compute is finished, if finished, reset the elapse cycle number
    def finish_computation(self):
        if self.elapse_cycle == 0:
            self.elapse_cycle = -1
            return True
        else:
            return False

    '''
        Functions related to reading stage
    '''
    def get_total_read(self):
        # need to check if total_read has been initialized
        # if not, calculate it before return
        if self.total_read == -1:
            total_read = 0
            if self.input_throughput != None:
                for throughput in self.input_throughput:
                    read_for_one_input = 1
                    for i in range(len(throughput)):
                        read_for_one_input *= throughput[i]

                    total_read += read_for_one_input

            self.total_read = total_read

        return self.total_read

    # return number of read still un-read
    def num_read_remain(self):
        total_read = self.get_total_read()

        # check if read_cnt has been initialized yet
        if self.read_cnt >= 0:
            return total_read - self.read_cnt
        else:
            return total_read


    # log num of reads happened in this reading cycle
    def read_from_input_buffer(self, read_cnt):
        # initialize it before count
        if self.read_cnt == -1:
            self.read_cnt = 0
        self.read_cnt += read_cnt
        self.sys_all_read_cnt += read_cnt

    # check if current reading stage is finished
    def check_read_finish(self):
        if self.read_cnt == self.get_total_read():
            return True
        else:
            return False

    '''
        Functions related to writing stage
    '''
    def get_total_write(self):
        # need to check if total_write has been initialized
        # if not, calculate it before return
        if self.total_write == -1:
            total_write = 1
            if self.output_throughput is not None:
                for i in range(len(self.output_throughput)):
                    total_write *= self.output_throughput[i]

            self.total_write = total_write

        return self.total_write

    # return number of write still un-read
    def num_write_remain(self):
        total_write = self.get_total_write()

        # check if write_cnt has been initialized yet
        if self.write_cnt >= 0:
            return total_write - self.write_cnt
        else:
            return total_write

    # log num of writes happened in this writing cycle
    def write_to_output_buffer(self, write_cnt):
        # initialize it before count
        if self.write_cnt == -1:
            self.write_cnt = 0
        prev_write_cnt = self.write_cnt
        self.write_cnt += write_cnt
        self.sys_all_write_cnt += write_cnt
        return prev_write_cnt

    # check if current writing stage is finished
    def check_write_finish(self):
        if self.write_cnt == self.get_total_write():
            # reset num_write before return
            self.write_cnt = -1
            return True
        else:
            return False

    def compute_energy(self):
        return 600*self.sys_all_compute_cycle

    def communication_energy(self):
        return int(R_W_ENERGY*(self.sys_all_write_cnt+self.sys_all_read_cnt))

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
        domain: int,    # whether is digital or analog
        location: int,  # location of this unit
        input_throughput: list,     # This is the input requirement in order to perform compute on this unit
        output_throughput: list,    # the number of element can be written out once one batch of compute is finished.
        clock: int,     # clock frequency
        energy: float,
        area: float,
        initial_delay: int, # # of clock cycles to propogate data before starting the first computation
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
        self.add_init_delay = False
        self.initial_delay = initial_delay
        self.delay = delay
        self.elapse_cycle = -1
        # parameters for reading stage
        self.read_cnt = -1 # num of input already being read for one compute
        self.total_read = -1 # total num of reads
        # parameters for writing stage
        self.write_cnt = -1 # num of output already being written for one compute
        self.total_write = -1 # total num of write

        self.input_hw_units = {}
        self.input_index_list = {}
        self.output_buffer_size = {}
        self.output_index_list = {}

        # performance counter
        self.sys_all_compute_cycle = 0
        self.sys_all_write_cnt = 0
        self.sys_all_read_cnt = 0

    '''
        # Input/output Data Dependency Configuration 

        All the input_/output_ related functions are used to define the dataflow.
        The input/output data indexes are used for HW unit to write data at the 
        correct location.
    '''
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
            raise Exception("[set_input_hw_unit]: each input sw_stage can only map to one hw_unit")


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

    def get_output_buffer_size(self, sw_stage):
        return self.output_buffer_size[sw_stage]

    # get/set output buffer index
    def get_output_buffer_index(self, sw_stage):
        return self.output_index_list[sw_stage]

    def set_output_buffer_index(self, sw_stage, output_buffer_index):
        self.output_index_list[sw_stage] = output_buffer_index

    '''
        # Compute-related Functions

        Those functions are used for cycle-level simulation, make sure each batch of 
        compute are finished based on the defined delay time.
    '''
    # initialize the cycle number that needs to be elapsed before writing the output
    def init_elapse_cycle(self):
        if self.add_init_delay:
            self.elapse_cycle = self.delay + self.initial_delay
            self.add_init_delay = False
        else:
            self.elapse_cycle = self.delay

    # process one cycle
    def process_one_cycle(self):
        self.elapse_cycle -= 1
        self.sys_all_compute_cycle += 1
        if ENABLE_DEBUG:
            print("[PROCESS]", self.name, "just compute 1 cycle, %d cycles left" % self.elapse_cycle)

    def start_init_delay(self):
        self.add_init_delay = True

    # check if the compute is finished, if finished, reset the elapse cycle number
    def finish_computation(self):
        if self.elapse_cycle == 0:
            self.elapse_cycle = -1
            return True
        else:
            return False

    def compute_energy(self):
        # print(self.name, self.energy, self.sys_all_compute_cycle, self.delay)
        return int(self.energy * self.sys_all_compute_cycle / self.delay)

    def communication_energy(self):
        return int(R_W_ENERGY*(self.sys_all_read_cnt+self.sys_all_write_cnt))

    '''
        Functions related to reading stage
    '''
    def get_total_read(self):
        # need to check if total_read has been initialized
        # if not, calculate it before return
        if self.total_read == -1:
            total_read = 0
            if self.input_throughput != None:
                for throughput in self.input_throughput:
                    read_for_one_input = 1
                    for i in range(len(throughput)):
                        read_for_one_input *= throughput[i]

                    total_read += read_for_one_input

            self.total_read = total_read

        return self.total_read

    # return number of read still un-read
    def num_read_remain(self):
        total_read = self.get_total_read()

        # check if read_cnt has been initialized yet
        if self.read_cnt >= 0:
            return total_read - self.read_cnt
        else:
            return total_read

    # log num of reads happened in this reading cycle
    def read_from_input_buffer(self, read_cnt):
        # initialize it before count
        if self.read_cnt == -1:
            self.read_cnt = 0
        self.read_cnt += read_cnt
        self.sys_all_read_cnt += read_cnt

    # check if current reading stage is finished
    def check_read_finish(self):
        if self.read_cnt == self.get_total_read():
            # reset num_read before return
            self.read_cnt = -1
            return True
        else:
            return False

    '''
        Functions related to writing stage
    '''
    def get_total_write(self):
        # need to check if total_write has been initialized
        # if not, calculate it before return
        if self.total_write == -1:
            total_write = 1
            if self.output_throughput is not None:
                for i in range(len(self.output_throughput)):
                    total_write *= self.output_throughput[i]

            self.total_write = total_write

        return self.total_write

    # return number of write still un-read
    def num_write_remain(self):
        total_write = self.get_total_write()

        # check if write_cnt has been initialized yet
        if self.write_cnt >= 0:
            return total_write - self.write_cnt
        else:
            return total_write

    # log num of writes happened in this writing cycle
    def write_to_output_buffer(self, write_cnt):
        # initialize it before count
        if self.write_cnt == -1:
            self.write_cnt = 0

        prev_write_cnt = self.write_cnt
        self.write_cnt += write_cnt
        self.sys_all_write_cnt += write_cnt
        return prev_write_cnt

    # check if current writing stage is finished
    def check_write_finish(self):
        if self.write_cnt == self.get_total_write():
            # reset num_write before return
            self.write_cnt = -1
            return True
        else:
            return False

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

'''
    Systolic Array, it is an unique architecture design.
'''
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

        self.add_init_delay = False
        self.initial_delay = size_dimension[0]
        self.delay = 10
        self.elapse_cycle = -1
        # parameters for reading stage
        self.read_cnt = -1 # num of input already being read for one compute
        self.total_read = -1 # total num of reads
        # parameters for writing stage
        self.write_cnt = -1 # num of output already being written for one compute
        self.total_write = -1 # total num of write

        # performance counter
        self.sys_all_compute_cycle = 0
        self.sys_all_write_cnt = 0
        self.sys_all_read_cnt = 0


    # needs to set the input and output buffer
    def set_input_buffer(self, input_buffer):
        self.input_buffer = input_buffer

    def set_output_buffer(self, output_buffer):
        self.output_buffer = output_buffer

    def config_throughput(self, input_size, output_size, stride, kernel_size, op_type):
        if ENABLE_DEBUG:
            print(
                "[SYSTOLIC] config: ", 
                "ifmap size: ", input_size, 
                "ofmap size: ", output_size, 
                "stride: ", stride, 
                "kernel size: ", kernel_size
            )

        if op_type == "Conv2D":
            # compute throughput dimension
            # when the input size is smaller than size_dimension, we should take input_size as throughput
            throughput_dimension_x = min(input_size[0]//stride, self.size_dimension[0])
            # same as throughput_dimension_x.
            throughput_dimension_y = min(input_size[1]//stride, self.size_dimension[1])
            # print("[SYSTOLIC]", throughput_dimension_x, throughput_dimension_y, self.size_dimension)

            # compute the input throughput, the input dependency for computing ofmap
            self.input_throughput = [
                (throughput_dimension_x*stride, throughput_dimension_y*stride, input_size[-1])
            ]
            
            # compute the output throughput
            self.output_throughput = (throughput_dimension_x, throughput_dimension_y, output_size[-1])

            # calculate the delay for one compute batch
            self.delay = kernel_size*kernel_size*input_size[-1]*output_size[-1]
        elif op_type == "DWConv2D":
            # compute throughput dimension
            # when the input size is smaller than size_dimension, we should take input_size as throughput
            throughput_dimension_x = min(input_size[0]//stride, self.size_dimension[0])
            # same as throughput_dimension_x.
            throughput_dimension_y = min(input_size[1]//stride, self.size_dimension[1])
            # print("[SYSTOLIC]", throughput_dimension_x, throughput_dimension_y, self.size_dimension)

            # compute the input throughput, the input dependency for computing ofmap
            self.input_throughput = [
                (throughput_dimension_x*stride, throughput_dimension_y*stride, input_size[-1])
            ]
            
            # compute the output throughput
            self.output_throughput = (throughput_dimension_x, throughput_dimension_y, output_size[-1])

            # calculate the delay for one compute batch
            self.delay = kernel_size*kernel_size*output_size[-1]
        elif op_type == "FC":
            self.input_throughput = [input_size]
            
            # compute the output throughput
            self.output_throughput = output_size

            fc_mac_cnt = input_size[0] * output_size[0]
            # calculate the delay for one compute batch
            self.delay = int(input_size[0] * output_size[0] / self.size_dimension[0])

        else:
            raise Exception("Unsupported op type when configuring throughput")

        if ENABLE_DEBUG:
            print(
                "[SYSTOLIC] input throughput: ", self.input_throughput,
                "output throughput: ", self.output_throughput,
                "compute delay: ", self.delay 
            )

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

    def get_output_buffer_size(self, sw_stage):
        return self.output_buffer_size[sw_stage]

    # get/set output buffer index
    def get_output_buffer_index(self, sw_stage):
        return self.output_index_list[sw_stage]

    def set_output_buffer_index(self, sw_stage, output_buffer_index):
        self.output_index_list[sw_stage] = output_buffer_index

    # initialize the cycle number that needs to be elapsed before writing the output
    def init_elapse_cycle(self):
        if self.add_init_delay:
            self.elapse_cycle = self.delay + self.initial_delay
            self.add_init_delay = False
        else:
            self.elapse_cycle = self.delay
    # process one cycle
    def process_one_cycle(self):
        self.elapse_cycle -= 1
        self.sys_all_compute_cycle += 1
        if ENABLE_DEBUG:
            print("[PROCESS]", self.name, "just compute 1 cycle, %d cycles left" % self.elapse_cycle)

    def start_init_delay(self):
        self.add_init_delay = True

    # check if the compute is finished, if finished, reset the elapse cycle number
    def finish_computation(self):
        if self.elapse_cycle == 0:
            self.elapse_cycle = -1
            return True
        else:
            return False

    def compute_energy(self):
        return int(self.energy * self.sys_all_compute_cycle)

    def communication_energy(self):
        return int(R_W_ENERGY*(self.sys_all_read_cnt+self.sys_all_write_cnt))
    '''
        Functions related to reading stage
    '''
    def get_total_read(self):
        total_read = 0
        if self.input_throughput != None:
            for throughput in self.input_throughput:
                read_for_one_input = 1
                for i in range(len(throughput)):
                    read_for_one_input *= throughput[i]

                total_read += read_for_one_input

        self.total_read = total_read

        return self.total_read

    # return number of read still un-read
    def num_read_remain(self):
        total_read = self.get_total_read()

        # check if read_cnt has been initialized yet
        if self.read_cnt >= 0:
            return total_read - self.read_cnt
        else:
            return total_read

    # log num of reads happened in this reading cycle
    def read_from_input_buffer(self, read_cnt):
        # initialize it before count
        if self.read_cnt == -1:
            self.read_cnt = 0
        self.read_cnt += read_cnt
        self.sys_all_read_cnt += read_cnt

    # check if current reading stage is finished
    def check_read_finish(self):
        if self.read_cnt == self.get_total_read():
            # reset num_read before return
            self.read_cnt = -1
            return True
        else:
            return False

        '''
        Functions related to writing stage
    '''
    def get_total_write(self):
        # need to check if total_write has been initialized
        # if not, calculate it before return
        # if self.total_write == -1:
        total_write = 1
        if self.output_throughput is not None:
            for i in range(len(self.output_throughput)):
                total_write *= self.output_throughput[i]

        self.total_write = total_write

        return self.total_write

    # return number of write still un-read
    def num_write_remain(self):
        total_write = self.get_total_write()

        # check if write_cnt has been initialized yet
        if self.write_cnt >= 0:
            return total_write - self.write_cnt
        else:
            return total_write

    # log num of writes happened in this writing cycle
    def write_to_output_buffer(self, write_cnt):
        # initialize it before count
        if self.write_cnt == -1:
            self.write_cnt = 0
        prev_write_cnt = self.write_cnt
        self.write_cnt += write_cnt
        self.sys_all_write_cnt += write_cnt
        return prev_write_cnt

    # check if current writing stage is finished
    def check_write_finish(self):
        if self.write_cnt == self.get_total_write():
            # reset num_write before return
            self.write_cnt = -1
            return True
        else:
            return False

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

'''
    Neural processor, it is an unique architecture design.
    It is a SIMD architecture that commonly exists in many mobile or 
    embedded architecture. 
    Curently, the data flow only supports output stationary.
'''
class NeuralProcessor(object):
    """docstring for NeuralProcessor"""
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
        super(NeuralProcessor, self).__init__()
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

        self.add_init_delay = False
        self.initial_delay = 0
        self.delay = 10
        self.elapse_cycle = -1
        # parameters for reading stage
        self.read_cnt = -1 # num of input already being read for one compute
        self.total_read = -1 # total num of reads
        # parameters for writing stage
        self.write_cnt = -1 # num of output already being written for one compute
        self.total_write = -1 # total num of write

        # performance counter
        self.sys_all_compute_cycle = 0
        self.sys_all_write_cnt = 0
        self.sys_all_read_cnt = 0


    # needs to set the input and output buffer
    def set_input_buffer(self, input_buffer):
        self.input_buffer = input_buffer

    def set_output_buffer(self, output_buffer):
        self.output_buffer = output_buffer

    def config_throughput(self, input_size, output_size, stride, kernel_size, op_type):
        if ENABLE_DEBUG:
            print(
                "[NEURALPROCESSOR] config: ", 
                "ifmap size: ", input_size, 
                "ofmap size: ", output_size, 
                "stride: ", stride, 
                "kernel size: ", kernel_size
            )

        if op_type == "Conv2D":
            # compute throughput dimension
            # when the input size is smaller than size_dimension, we should take input_size as throughput
            throughput_dimension_x = min(input_size[0]//stride, self.size_dimension[0])
            # same as throughput_dimension_x.
            throughput_dimension_y = min(input_size[1]//stride, self.size_dimension[1])
            # print("[SYSTOLIC]", throughput_dimension_x, throughput_dimension_y, self.size_dimension)

            # compute the input throughput, the input dependency for computing ofmap
            self.input_throughput = [
                (throughput_dimension_x*stride, throughput_dimension_y*stride, input_size[-1])
            ]
            
            # compute the output throughput
            self.output_throughput = (throughput_dimension_x, throughput_dimension_y, output_size[-1])

            # calculate the delay for one compute batch
            self.delay = kernel_size*kernel_size*input_size[-1]*output_size[-1]
        elif op_type == "DWConv2D":
            # compute throughput dimension
            # when the input size is smaller than size_dimension, we should take input_size as throughput
            throughput_dimension_x = min(input_size[0]//stride, self.size_dimension[0])
            # same as throughput_dimension_x.
            throughput_dimension_y = min(input_size[1]//stride, self.size_dimension[1])
            # print("[SYSTOLIC]", throughput_dimension_x, throughput_dimension_y, self.size_dimension)

            # compute the input throughput, the input dependency for computing ofmap
            self.input_throughput = [
                (throughput_dimension_x*stride, throughput_dimension_y*stride, input_size[-1])
            ]
            
            # compute the output throughput
            self.output_throughput = (throughput_dimension_x, throughput_dimension_y, output_size[-1])

            # calculate the delay for one compute batch
            self.delay = kernel_size*kernel_size*output_size[-1]
        elif op_type == "FC":
            self.input_throughput = [input_size]
            
            # compute the output throughput
            self.output_throughput = output_size

            fc_mac_cnt = input_size[0] * output_size[0]
            # calculate the delay for one compute batch
            self.delay = int(input_size[0] * output_size[0] / self.size_dimension[0])

        else:
            raise Exception("Unsupported op type when configuring throughput")

        if ENABLE_DEBUG:
            print(
                "[NEURALPROCESSOR] input throughput: ", self.input_throughput,
                "output throughput: ", self.output_throughput,
                "compute delay: ", self.delay 
            )

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

    def get_output_buffer_size(self, sw_stage):
        return self.output_buffer_size[sw_stage]

    # get/set output buffer index
    def get_output_buffer_index(self, sw_stage):
        return self.output_index_list[sw_stage]

    def set_output_buffer_index(self, sw_stage, output_buffer_index):
        self.output_index_list[sw_stage] = output_buffer_index

    # initialize the cycle number that needs to be elapsed before writing the output
    def init_elapse_cycle(self):
        if self.add_init_delay:
            self.elapse_cycle = self.delay + self.initial_delay
            self.add_init_delay = False
        else:
            self.elapse_cycle = self.delay
    # process one cycle
    def process_one_cycle(self):
        self.elapse_cycle -= 1
        self.sys_all_compute_cycle += 1
        if ENABLE_DEBUG:
            print("[PROCESS]", self.name, "just compute 1 cycle, %d cycles left" % self.elapse_cycle)

    def start_init_delay(self):
        self.add_init_delay = True

    # check if the compute is finished, if finished, reset the elapse cycle number
    def finish_computation(self):
        if self.elapse_cycle == 0:
            self.elapse_cycle = -1
            return True
        else:
            return False

    def compute_energy(self):
        return int(self.energy * self.sys_all_compute_cycle)

    def communication_energy(self):
        return int(
            R_W_ENERGY*(self.sys_all_read_cnt+self.sys_all_write_cnt)
        )
    '''
        Functions related to reading stage
    '''
    def get_total_read(self):
        total_read = 0
        if self.input_throughput != None:
            for throughput in self.input_throughput:
                read_for_one_input = 1
                for i in range(len(throughput)):
                    read_for_one_input *= throughput[i]

                total_read += read_for_one_input

        self.total_read = total_read

        return self.total_read

    # return number of read still un-read
    def num_read_remain(self):
        total_read = self.get_total_read()

        # check if read_cnt has been initialized yet
        if self.read_cnt >= 0:
            return total_read - self.read_cnt
        else:
            return total_read

    # log num of reads happened in this reading cycle
    def read_from_input_buffer(self, read_cnt):
        # initialize it before count
        if self.read_cnt == -1:
            self.read_cnt = 0
        self.read_cnt += read_cnt
        self.sys_all_read_cnt += read_cnt

    # check if current reading stage is finished
    def check_read_finish(self):
        if self.read_cnt == self.get_total_read():
            # reset num_read before return
            self.read_cnt = -1
            return True
        else:
            return False

        '''
        Functions related to writing stage
    '''
    def get_total_write(self):
        # need to check if total_write has been initialized
        # if not, calculate it before return
        # if self.total_write == -1:
        total_write = 1
        if self.output_throughput is not None:
            for i in range(len(self.output_throughput)):
                total_write *= self.output_throughput[i]

        self.total_write = total_write

        return self.total_write

    # return number of write still un-read
    def num_write_remain(self):
        total_write = self.get_total_write()

        # check if write_cnt has been initialized yet
        if self.write_cnt >= 0:
            return total_write - self.write_cnt
        else:
            return total_write

    # log num of writes happened in this writing cycle
    def write_to_output_buffer(self, write_cnt):
        # initialize it before count
        if self.write_cnt == -1:
            self.write_cnt = 0
        prev_write_cnt = self.write_cnt
        self.write_cnt += write_cnt
        self.sys_all_write_cnt += write_cnt
        return prev_write_cnt

    # check if current writing stage is finished
    def check_write_finish(self):
        if self.write_cnt == self.get_total_write():
            # reset num_write before return
            self.write_cnt = -1
            return True
        else:
            return False

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name