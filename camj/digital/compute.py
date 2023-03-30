"""Digital Compute Library

This module defines the digital compute interface. It contains three types of compute units
which can be used in digital simulation.
"""
import numpy as np
from camj.general.flags import *

class ADC(object):
    """ADC compute unit

    ADC is special in digital domain because it serves as an interface between digital and analog domain.
    Here, to perform digital simulation, we assume the computation starts with ADC. Users need
    to define ADC to launch digital simulation.

    Args:
        name(str): name of this class.
        output_pixels_per_cycle (tuple): the output pixel rate per cycle. It should be in ``(H, W, C)`` format.
        location: defines the location of the ADC. see ``general.enum`` for more details.
        energy_per_pixel: the energy consumption generated in digital domain per pixel.

    """
    def __init__(
        self,
        name: str, 
        output_pixels_per_cycle: tuple,
        location,
        energy_per_pixel = 600
    ):
        super(ADC, self).__init__()
        self.name = name

        # check output pixels per cycle is a 3D tuple.
        assert len(output_pixels_per_cycle) == 3, "Parameter 'output_pixels_per_cycle' should be a tuple of length 3!"
        self.input_pixels_per_cycle = None
        self.output_pixels_per_cycle = (
            output_pixels_per_cycle[1],
            output_pixels_per_cycle[0],
            output_pixels_per_cycle[2]
        ) # covert (h, w, c) to internal representation (x, y, z)

        self.location = location
        self.energy_per_pixel = energy_per_pixel
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

    #################################################
    #               Public functions                #
    #################################################
    def set_input_buffer(self, input_buffer):
        """Set Input Buffer
            
        This function sets the input buffer for this compute unit. Each compute can have
        one input buffer, call this function multiple times will overwrite the old input
        buffer.

        Args:
            input_buffer: input buffer object for this compute instance.

        Returns:
            None
        """
        self.input_buffer = input_buffer
        input_buffer._add_access_unit(self.name)

    def set_output_buffer(self, output_buffer):
        """Set Output Buffer

        This function sets the output buffer for this compute unit. Each compute can have
        one output buffer, call this function multiple times will overwrite the old output
        buffer.

        Args:
            output_buffer: output buffer object for this compute instance.

        Returns:
            None
        """
        self.output_buffer = output_buffer
        output_buffer._add_access_unit(self.name)

    def get_total_read(self):
        """Calculate number of reads before output the given number of pixels defined by users.

        Returns:
            Number of Reads (int)
        """
        # need to check if total_read has been initialized
        # if not, calculate it before return
        if self.total_read == -1:
            total_read = 0
            if self.input_pixels_per_cycle != None:
                for throughput in self.input_pixels_per_cycle:
                    read_for_one_input = 1
                    for i in range(len(throughput)):
                        read_for_one_input *= throughput[i]

                    total_read += read_for_one_input

            self.total_read = total_read

        return self.total_read

    def get_total_write(self):
        """Calculate number of writes to output the given number of pixels defined by users.

        Returns:
            Number of Write (int)
        """
        # need to check if total_write has been initialized
        # if not, calculate it before return
        if self.total_write == -1:
            total_write = 1
            if self.output_pixels_per_cycle is not None:
                for i in range(len(self.output_pixels_per_cycle)):
                    total_write *= self.output_pixels_per_cycle[i]

            self.total_write = total_write

        return self.total_write

    def compute_energy(self):
        """Total Compute Energy

        This function calculates the total compute energy for this compute instance.
        CamJ simulator calls this function after the simulation is finished.

        Mathematically Expression:
            Total Compute Energy = Energy per Pixel * Output Pixels

        Returns:
            Compute energy number in pJ (int)
        """
        return int(self.energy_per_pixel * self.sys_all_compute_cycle * self.total_write)


    #################################################
    #               Private functions               #
    #################################################
    def _init_output_buffer_index(self, sw_stage, buffer_size):
        self.output_buffer_size[sw_stage] = buffer_size
        self.output_index_list[sw_stage] = []
        for i in buffer_size:
            self.output_index_list[sw_stage].append(0)

    def _get_output_buffer_size(self, sw_stage):
        return self.output_buffer_size[sw_stage]

    def _get_output_buffer_index(self, sw_stage):
        return self.output_index_list[sw_stage]

    def _set_output_buffer_index(self, sw_stage, output_buffer_index):
        self.output_index_list[sw_stage] = output_buffer_index

    # initialize the cycle number that needs to be elapsed before writing the output
    def _init_elapse_cycle(self):
        self.elapse_cycle = self.delay

    # process one cycle
    def _process_one_cycle(self):
        self.elapse_cycle -= 1
        self.sys_all_compute_cycle += 1

    # dummy function
    def _start_init_delay(self):
        pass

    # check if the compute is finished, if finished, reset the elapse cycle number
    def _finish_computation(self):
        if self.elapse_cycle == 0:
            self.elapse_cycle = -1
            return True
        else:
            return False

    '''
        Functions related to reading stage
    '''
    # return number of read still un-read
    def _num_read_remain(self):
        total_read = self.get_total_read()

        # check if read_cnt has been initialized yet
        if self.read_cnt >= 0:
            return total_read - self.read_cnt
        else:
            return total_read

    # log num of reads happened in this reading cycle
    def _read_from_input_buffer(self, read_cnt):
        # initialize it before count
        if self.read_cnt == -1:
            self.read_cnt = 0
        self.read_cnt += read_cnt

    # check if current reading stage is finished
    def _check_read_finish(self):
        if self.read_cnt == self.get_total_read():
            return True
        else:
            return False

    '''
        Functions related to writing stage
    '''
    # return number of write still un-read
    def _num_write_remain(self):
        total_write = self.get_total_write()

        # check if write_cnt has been initialized yet
        if self.write_cnt >= 0:
            return total_write - self.write_cnt
        else:
            return total_write

    # log num of writes happened in this writing cycle
    def _write_to_output_buffer(self, write_cnt):
        # initialize it before count
        if self.write_cnt == -1:
            self.write_cnt = 0
        prev_write_cnt = self.write_cnt
        self.write_cnt += write_cnt
        return prev_write_cnt

    # check if current writing stage is finished
    def _check_write_finish(self):
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


class ComputeUnit(object):
    """Generic Compute Unit Interface

    This is the generic Compute Unit interface for digital domain. It can be used to
    model any digital compute hardware that performs stencil operations.

    Args:
        name(str): name of this class.
        location: defines the location of the ADC. see ``general.enum`` for more details.
        output_pixels_per_cycle (list): the input pixel rate per cycle in order to perform computation.
            It should be a list of tuple. Each tuple should be in ``(H, W, C)`` format.
        output_pixels_per_cycle (tuple): the output pixel rate per cycle. It should be in ``(H, W, C)`` format.
        energy_per_cycle (float): the average energy per cycle in unit of pJ.
        num_of_stages (int): number of stage of this compute unit in the pipeline.

    Examples:
        To instantiate a ``3x3x1`` convolution operation with 3-stage pipeline. Each cycle, 
        this compute unit takes ``1x3x1`` inputs and output ``1x1x1``. When fully pipelined,
        this compute unit consumes 9 pJ (9 operations, each takes 1 pJ).

        >>> ComputeUnit(
            name = "ConvUnit",
            location = ProcessorLocation.COMPUTE_LAYER,
            input_pixels_per_cycle = [(1, 3, 1)],
            output_pixels_per_cycle = (1, 1, 1),
            energy_per_cycle = 9,   # pJ
            num_of_stages = 3,      # 3-stage pipeline
        ) 
    """
    def __init__(
        self,
        name: str,
        location: int,  # location of this unit
        input_pixels_per_cycle: list,     # This is the input requirement in order to perform compute on this unit
        output_pixels_per_cycle: list,    # the number of element can be written out once one batch of compute is finished.
        energy_per_cycle: float,   # the average energy per cycle
        num_of_stages: int,        # number of stage in the pipeline.
    ):
        super(ComputeUnit, self).__init__()
        # assign variables
        self.name = name
        self.location = location
        self.energy_per_cycle = energy_per_cycle

        # covert (h, w, c) to internal representation (x, y, z)
        self.input_pixels_per_cycle = _convert_hwc_to_xyz(name, input_pixels_per_cycle)

        # check output pixels per cycle is a 3D tuple.
        assert len(output_pixels_per_cycle) == 3, "Parameter 'output_pixels_per_cycle' should be a tuple of length 3!"
        self.output_pixels_per_cycle = (
            output_pixels_per_cycle[1],
            output_pixels_per_cycle[0],
            output_pixels_per_cycle[2]
        ) # covert (h, w, c) to internal representation (x, y, z)
        
        # setup the delay for the entire compute
        self.add_init_delay = False
        self.initial_delay = num_of_stages - 1
        self.delay = 1
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

    #################################################
    #               Public functions                #
    #################################################

    """Input/output Data Dependency Configuration 

        All the input_/output_ related functions are used to define the dataflow.
        The input/output data indexes are used for HW unit to write data at the 
        correct location.
    """
    def set_input_buffer(self, input_buffer):
        """Set Input Buffer
            
        This function sets the input buffer for this compute unit. Each compute can have
        one input buffer, call this function multiple times will overwrite the old input
        buffer.

        Args:
            input_buffer: input buffer object for this compute instance.

        Returns:
            None
        """
        self.input_buffer = input_buffer
        input_buffer._add_access_unit(self.name)

    def set_output_buffer(self, output_buffer):
        """Set Output Buffer

        This function sets the output buffer for this compute unit. Each compute can have
        one output buffer, call this function multiple times will overwrite the old output
        buffer.

        Args:
            output_buffer: output buffer object for this compute instance.

        Returns:
            None
        """
        self.output_buffer = output_buffer
        output_buffer._add_access_unit(self.name)

    def compute_energy(self):
        """Total Compute Energy

        This function calculates the total compute energy for this compute instance.
        CamJ simulator calls this function after the simulation is finished.

        Mathematically Expression:
            Total Compute Energy = Energy per cycle * Compute Cycles

        Returns:
            Compute energy number in pJ (int)
        """
        # print(self.name, self.energy_per_cycle, self.sys_all_compute_cycle)
        return int(self.energy_per_cycle * self.sys_all_compute_cycle)

    def get_total_read(self):
        """Calculate number of reads before output the given number of pixels defined by users.

        Returns:
            Number of Reads (int)
        """
        # need to check if total_read has been initialized
        # if not, calculate it before return
        if self.total_read == -1:
            total_read = 0
            if self.input_pixels_per_cycle != None:
                for throughput in self.input_pixels_per_cycle:
                    read_for_one_input = 1
                    for i in range(len(throughput)):
                        read_for_one_input *= throughput[i]

                    total_read += read_for_one_input

            self.total_read = total_read

        return self.total_read

    def get_total_write(self):
        """Calculate number of writes to output the given number of pixels defined by users.

        Returns:
            Number of Write (int)
        """
        # need to check if total_write has been initialized
        # if not, calculate it before return
        if self.total_write == -1:
            total_write = 1
            if self.output_pixels_per_cycle is not None:
                for i in range(len(self.output_pixels_per_cycle)):
                    total_write *= self.output_pixels_per_cycle[i]

            self.total_write = total_write

        return self.total_write

    #################################################
    #               Private functions               #
    #################################################
    # set the input hw units, the final input hw units is a list,
    # we assume multiple hw units as input
    def _set_input_hw_unit(self, sw_stage, hw_unit):
        if sw_stage not in self.input_hw_units:
            self.input_hw_units[sw_stage] = [hw_unit]
        else:
            raise Exception("[set_input_hw_unit]: each input sw_stage can only map to one hw_unit")

    # initialize input buffer index, so that we know where to the next data
    # the buffer index will be indexed using (source hw unit, sw stage)
    def _init_input_buffer_index(self, src_hw_unit, sw_stage, buffer_size):
        self.input_index_list[src_hw_unit, sw_stage] = []
        for i in buffer_size:
            self.input_index_list[src_hw_unit, sw_stage].append(0)

    # get/set input buffer index
    def _get_input_buffer_index(self, src_hw_unit, sw_stage):
        return self.input_index_list[src_hw_unit, sw_stage]

    def _set_input_buffer_index(self, src_hw_unit, sw_stage, input_buffer_index):
        self.input_index_list[src_hw_unit, sw_stage] = input_buffer_index

    # initial output buffer index, here only sw stage is used as index,
    # because we consider only one output buffer
    def _init_output_buffer_index(self, sw_stage, buffer_size):
        self.output_buffer_size[sw_stage] = buffer_size
        self.output_index_list[sw_stage] = []
        for i in buffer_size:
            self.output_index_list[sw_stage].append(0)

    def _get_output_buffer_size(self, sw_stage):
        return self.output_buffer_size[sw_stage]

    # get/set output buffer index
    def _get_output_buffer_index(self, sw_stage):
        return self.output_index_list[sw_stage]

    def _set_output_buffer_index(self, sw_stage, output_buffer_index):
        self.output_index_list[sw_stage] = output_buffer_index

    """Compute-related Functions

        Those functions are used for cycle-level simulation, make sure each batch of 
        compute are finished based on the defined delay time.
    """
    # initialize the cycle number that needs to be elapsed before writing the output
    def _init_elapse_cycle(self):
        if self.add_init_delay:
            self.elapse_cycle = self.delay + self.initial_delay
            self.add_init_delay = False
        else:
            self.elapse_cycle = self.delay

    # process one cycle
    def _process_one_cycle(self):
        self.elapse_cycle -= 1
        self.sys_all_compute_cycle += 1
        if ENABLE_DEBUG:
            print("[PROCESS]", self.name, "just compute 1 cycle, %d cycles left" % self.elapse_cycle)

    def _start_init_delay(self):
        self.add_init_delay = True

    # check if the compute is finished, if finished, reset the elapse cycle number
    def _finish_computation(self):
        if self.elapse_cycle == 0:
            self.elapse_cycle = -1
            return True
        else:
            return False

    """
        Functions related to reading stage
    """
    # return number of read still un-read
    def _num_read_remain(self):
        total_read = self.get_total_read()

        # check if read_cnt has been initialized yet
        if self.read_cnt >= 0:
            return total_read - self.read_cnt
        else:
            return total_read

    # log num of reads happened in this reading cycle
    def _read_from_input_buffer(self, read_cnt):
        # initialize it before count
        if self.read_cnt == -1:
            self.read_cnt = 0
        self.read_cnt += read_cnt

    # check if current reading stage is finished
    def _check_read_finish(self):
        if self.read_cnt == self.get_total_read():
            # reset num_read before return
            self.read_cnt = -1
            return True
        else:
            return False

    """
        Functions related to writing stage
    """
    # return number of write still un-read
    def _num_write_remain(self):
        total_write = self.get_total_write()

        # check if write_cnt has been initialized yet
        if self.write_cnt >= 0:
            return total_write - self.write_cnt
        else:
            return total_write

    # log num of writes happened in this writing cycle
    def _write_to_output_buffer(self, write_cnt):
        # initialize it before count
        if self.write_cnt == -1:
            self.write_cnt = 0

        prev_write_cnt = self.write_cnt
        self.write_cnt += write_cnt
        return prev_write_cnt

    # check if current writing stage is finished
    def _check_write_finish(self):
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


class SystolicArray(object):
    """SystolicArray

    This class emulate a classic architecture design, systolic array.

    Args:
        name(str): name of this class.
        location: defines the location of the ADC. see ``general.enum.ProcessorLocation`` for more details.
        size_dimension (tuple): the dimension of the systolic array in a format of ``(H, W)``.
        energy_per_cycle (float): the average energy per cycle in unit of pJ.

    Example:
        To instantiate a ``16x16`` systolic array

        >>> SystolicArray(
            name = "SystolicArray",
            location = ProcessorLocation.COMPUTE_LAYER,
            size_dimension = (16, 16),
            energy_per_cycle = 0.5 * 16 *16, # 0.5 pJ per MAC op
        )
    """
    def __init__(
        self,
        name,
        location,
        size_dimension,
        energy_per_cycle,
    ):
        super(SystolicArray, self).__init__()
        # store configs
        self.name = name
        self.location = location
        self.size_dimension = size_dimension
        self.energy_per_cycle = energy_per_cycle

        # simulation setup
        self.input_hw_units = {}
        self.input_index_list = {}

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

    #################################################
    #               Public functions                #
    #################################################
    # needs to set the input and output buffer
    def set_input_buffer(self, input_buffer):
        """Set Input Buffer
            
        This function sets the input buffer for this compute unit. Each compute can have
        one input buffer, call this function multiple times will overwrite the old input
        buffer.

        Args:
            input_buffer: input buffer object for this compute instance.

        Returns:
            None
        """
        self.input_buffer = input_buffer
        input_buffer._add_access_unit(self.name)

    def set_output_buffer(self, output_buffer):
        """Set Output Buffer

        This function sets the output buffer for this compute unit. Each compute can have
        one output buffer, call this function multiple times will overwrite the old output
        buffer.

        Args:
            output_buffer: output buffer object for this compute instance.

        Returns:
            None
        """
        self.output_buffer = output_buffer
        output_buffer._add_access_unit(self.name)

    def compute_energy(self):
        """Total Compute Energy

        This function calculates the total compute energy for this compute instance.
        CamJ simulator calls this function after the simulation is finished.

        Mathematically Expression:
            Total Compute Energy = Energy per cycle * Compute Cycles

        Returns:
            Compute energy number in pJ (int)
        """
        return int(self.energy_per_cycle * self.sys_all_compute_cycle)

    def get_total_read(self):
        """Calculate number of reads before output the given number of pixels defined by users.

        Returns:
            Number of Reads (int)
        """
        total_read = 0
        if self.input_pixels_per_cycle != None:
            for throughput in self.input_pixels_per_cycle:
                read_for_one_input = 1
                for i in range(len(throughput)):
                    read_for_one_input *= throughput[i]

                total_read += read_for_one_input

        self.total_read = total_read

        return self.total_read

    def get_total_write(self):
        """Calculate number of writes to output the given number of pixels defined by users.

        Returns:
            Number of Write (int)
        """
        # need to check if total_write has been initialized
        # if not, calculate it before return
        total_write = 1
        if self.output_pixels_per_cycle is not None:
            for i in range(len(self.output_pixels_per_cycle)):
                total_write *= self.output_pixels_per_cycle[i]

        self.total_write = total_write

        return self.total_write

    #################################################
    #               Private functions               #
    #################################################

    def _config_throughput(self, input_size, output_size, stride, kernel_size, op_type):
        if ENABLE_DEBUG:
            print(
                "[SYSTOLIC] config: ", 
                "ifmap size (x, y, z): ", input_size, 
                "ofmap size (x, y, z): ", output_size, 
                "stride (x, y, z): ", stride, 
                "kernel size (x, y, z): ", kernel_size
            )

        if op_type == "Conv2D":
            # compute throughput dimension
            # when the input size is smaller than size_dimension, we should take input_size as throughput
            throughput_dimension_x = min(input_size[0]//stride[0], self.size_dimension[0])
            # same as throughput_dimension_x.
            throughput_dimension_y = min(input_size[1]//stride[1], self.size_dimension[1])
            # print("[SYSTOLIC]", throughput_dimension_x, throughput_dimension_y, self.size_dimension)

            # compute the input throughput, the input dependency for computing ofmap
            self.input_pixels_per_cycle = [
                (
                    throughput_dimension_x * stride[0], 
                    throughput_dimension_y * stride[1], 
                    input_size[-1] * 1
                )
            ]
            
            # compute the output throughput
            self.output_pixels_per_cycle = (throughput_dimension_x, throughput_dimension_y, 1)

            # calculate the delay for one compute batch
            self.delay = kernel_size[0] * kernel_size[1] * input_size[-1] * 1
        elif op_type == "DWConv2D":
            # compute throughput dimension
            # when the input size is smaller than size_dimension, we should take input_size as throughput
            throughput_dimension_x = min(input_size[0]//stride[0], self.size_dimension[0])
            # same as throughput_dimension_x.
            throughput_dimension_y = min(input_size[1]//stride[1], self.size_dimension[1])
            # print("[SYSTOLIC]", throughput_dimension_x, throughput_dimension_y, self.size_dimension)

            # compute the input throughput, the input dependency for computing ofmap
            self.input_pixels_per_cycle = [
                (
                    throughput_dimension_x * stride[0], 
                    throughput_dimension_y * stride[1], 
                    input_size[-1] * 1
                )
            ]
            
            # compute the output throughput
            self.output_pixels_per_cycle = (throughput_dimension_x, throughput_dimension_y, 1)

            # calculate the delay for one compute batch
            self.delay = kernel_size[0] * kernel_size[1] * 1
        elif op_type == "FC":
            self.input_pixels_per_cycle = [input_size]
            
            # compute the output throughput
            self.output_pixels_per_cycle = output_size

            fc_mac_cnt = input_size[0] * output_size[0]
            # calculate the delay for one compute batch
            self.delay = int(input_size[0] * output_size[0] / self.size_dimension[0])

        else:
            raise Exception("Unsupported op type when configuring throughput")

        if ENABLE_DEBUG:
            print(
                "[SYSTOLIC] input throughput: ", self.input_pixels_per_cycle,
                "output throughput: ", self.output_pixels_per_cycle,
                "compute delay: ", self.delay 
            )

    # set the input hw units, the final input hw units is a list,
    # we assume multiple hw units as input
    def _set_input_hw_unit(self, sw_stage, hw_unit):
        if sw_stage not in self.input_hw_units:
            self.input_hw_units[sw_stage] = [hw_unit]
        else:
            self.input_hw_units[sw_stage].append(hw_unit)

    # initialize input buffer index, so that we know where to the next data
    # the buffer index will be indexed using (source hw unit, sw stage)
    def _init_input_buffer_index(self, src_hw_unit, sw_stage, buffer_size):
        self.input_index_list[src_hw_unit, sw_stage] = []
        for i in buffer_size:
            self.input_index_list[src_hw_unit, sw_stage].append(0)

    # get/set input buffer index
    def _get_input_buffer_index(self, src_hw_unit, sw_stage):
        return self.input_index_list[src_hw_unit, sw_stage]

    def _set_input_buffer_index(self, src_hw_unit, sw_stage, input_buffer_index):
        self.input_index_list[src_hw_unit, sw_stage] = input_buffer_index

    # initial output buffer index, here only sw stage is used as index,
    # because we consider only one output buffer
    def _init_output_buffer_index(self, sw_stage, buffer_size):
        
        self.output_pixels_per_cycle = np.ones_like(buffer_size)
        self.output_pixels_per_cycle[0] = self.size_dimension[0]

        self.output_buffer_size[sw_stage] = buffer_size
        
        self.output_index_list[sw_stage] = []
        for i in buffer_size:
            self.output_index_list[sw_stage].append(0)

    def _get_output_buffer_size(self, sw_stage):
        return self.output_buffer_size[sw_stage]

    # get/set output buffer index
    def _get_output_buffer_index(self, sw_stage):
        return self.output_index_list[sw_stage]

    def _set_output_buffer_index(self, sw_stage, output_buffer_index):
        self.output_index_list[sw_stage] = output_buffer_index

    # initialize the cycle number that needs to be elapsed before writing the output
    def _init_elapse_cycle(self):
        if self.add_init_delay:
            self.elapse_cycle = self.delay + self.initial_delay
            self.add_init_delay = False
        else:
            self.elapse_cycle = self.delay
    # process one cycle
    def _process_one_cycle(self):
        self.elapse_cycle -= 1
        self.sys_all_compute_cycle += 1
        if ENABLE_DEBUG:
            print("[PROCESS]", self.name, "just compute 1 cycle, %d cycles left" % self.elapse_cycle)

    def _start_init_delay(self):
        self.add_init_delay = True

    # check if the compute is finished, if finished, reset the elapse cycle number
    def _finish_computation(self):
        if self.elapse_cycle == 0:
            self.elapse_cycle = -1
            return True
        else:
            return False

    """
        Functions related to reading stage
    """
    # return number of read still un-read
    def _num_read_remain(self):
        total_read = self.get_total_read()

        # check if read_cnt has been initialized yet
        if self.read_cnt >= 0:
            return total_read - self.read_cnt
        else:
            return total_read

    # log num of reads happened in this reading cycle
    def _read_from_input_buffer(self, read_cnt):
        # initialize it before count
        if self.read_cnt == -1:
            self.read_cnt = 0
        self.read_cnt += read_cnt

    # check if current reading stage is finished
    def _check_read_finish(self):
        if self.read_cnt == self.get_total_read():
            # reset num_read before return
            self.read_cnt = -1
            return True
        else:
            return False

    """
        Functions related to writing stage
    """
    # return number of write still un-read
    def _num_write_remain(self):
        total_write = self.get_total_write()

        # check if write_cnt has been initialized yet
        if self.write_cnt >= 0:
            return total_write - self.write_cnt
        else:
            return total_write

    # log num of writes happened in this writing cycle
    def _write_to_output_buffer(self, write_cnt):
        # initialize it before count
        if self.write_cnt == -1:
            self.write_cnt = 0
        prev_write_cnt = self.write_cnt
        self.write_cnt += write_cnt
        return prev_write_cnt

    # check if current writing stage is finished
    def _check_write_finish(self):
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


class SIMDProcessor(object):
    """SIMD Processor

    It is a SIMD architecture that commonly exists in many mobile or embedded architecture 
    for DNN acceleration. Curently, the data flow only supports output stationary.

    Args:
        name(str): name of this class.
        location: defines the location of the ADC. see ``general.enum.ProcessorLocation`` for more details.
        size_dimension (tuple): the dimension of the systolic array in a format of ``(H, W)``.
        energy_per_cycle (float): the average energy per cycle in unit of pJ.

    """
    def __init__(
        self,
        name,
        location,
        size_dimension,
        energy_per_cycle
    ):
        super(SIMDProcessor, self).__init__()
        # store configs
        self.name = name
        self.location = location
        self.size_dimension = size_dimension
        self.energy_per_cycle = energy_per_cycle

        self.input_hw_units = {}
        self.input_index_list = {}
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


        # simulation setup
        self.input_hw_units = {}
        self.input_index_list = {}

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

    #################################################
    #               Public functions                #
    #################################################
    # needs to set the input and output buffer
    def set_input_buffer(self, input_buffer):
        """Set Input Buffer
            
        This function sets the input buffer for this compute unit. Each compute can have
        one input buffer, call this function multiple times will overwrite the old input
        buffer.

        Args:
            input_buffer: input buffer object for this compute instance.

        Returns:
            None
        """
        self.input_buffer = input_buffer
        input_buffer._add_access_unit(self.name)

    def set_output_buffer(self, output_buffer):
        """Set Output Buffer

        This function sets the output buffer for this compute unit. Each compute can have
        one output buffer, call this function multiple times will overwrite the old output
        buffer.

        Args:
            output_buffer: output buffer object for this compute instance.

        Returns:
            None
        """
        self.output_buffer = output_buffer
        output_buffer._add_access_unit(self.name)

    def compute_energy(self):
        """Total Compute Energy

        This function calculates the total compute energy for this compute instance.
        CamJ simulator calls this function after the simulation is finished.

        Mathematically Expression:
            Total Compute Energy = Energy per cycle * Compute Cycles

        Returns:
            Compute energy number in pJ (int)
        """
        return int(self.energy_per_cycle * self.sys_all_compute_cycle)

    def get_total_read(self):
        """Calculate number of reads before output the given number of pixels defined by users.

        Returns:
            Number of Reads (int)
        """
        total_read = 0
        if self.input_pixels_per_cycle != None:
            for throughput in self.input_pixels_per_cycle:
                read_for_one_input = 1
                for i in range(len(throughput)):
                    read_for_one_input *= throughput[i]

                total_read += read_for_one_input

        self.total_read = total_read

        return self.total_read

    def get_total_write(self):
        """Calculate number of writes to output the given number of pixels defined by users.

        Returns:
            Number of Write (int)
        """
        # need to check if total_write has been initialized
        # if not, calculate it before return
        total_write = 1
        if self.output_pixels_per_cycle is not None:
            for i in range(len(self.output_pixels_per_cycle)):
                total_write *= self.output_pixels_per_cycle[i]

        self.total_write = total_write

        return self.total_write

    #################################################
    #               Private functions               #
    #################################################

    def _config_throughput(self, input_size, output_size, stride, kernel_size, op_type):
        if ENABLE_DEBUG:
            print(
                "[SIMDProcessor] config: ", 
                "ifmap size (x, y, z): ", input_size, 
                "ofmap size (x, y, z): ", output_size, 
                "stride (x, y, z): ", stride, 
                "kernel size (x, y, z): ", kernel_size
            )

        if op_type == "Conv2D":
            # compute throughput dimension
            # when the input size is smaller than size_dimension, we should take input_size as throughput
            throughput_dimension_x = min(input_size[0]//stride[0], self.size_dimension[0])
            # same as throughput_dimension_x.
            throughput_dimension_y = min(input_size[1]//stride[1], self.size_dimension[1])
            # print("[SIMDProcessor]", throughput_dimension_x, throughput_dimension_y, self.size_dimension)

            # compute the input throughput, the input dependency for computing ofmap
            self.input_pixels_per_cycle = [
                (
                    throughput_dimension_x * stride[0], 
                    throughput_dimension_y * stride[1], 
                    input_size[-1] * 1
                )
            ]
            
            # compute the output throughput
            self.output_pixels_per_cycle = (throughput_dimension_x, throughput_dimension_y, 1)

            # calculate the delay for one compute batch
            self.delay = kernel_size[0] * kernel_size[1] * input_size[-1] * 1
        elif op_type == "DWConv2D":
            # compute throughput dimension
            # when the input size is smaller than size_dimension, we should take input_size as throughput
            throughput_dimension_x = min(input_size[0]//stride[0], self.size_dimension[0])
            # same as throughput_dimension_x.
            throughput_dimension_y = min(input_size[1]//stride[1], self.size_dimension[1])
            # print("[SIMDProcessor]", throughput_dimension_x, throughput_dimension_y, self.size_dimension)

            # compute the input throughput, the input dependency for computing ofmap
            self.input_pixels_per_cycle = [
                (
                    throughput_dimension_x * stride[0], 
                    throughput_dimension_y * stride[1], 
                    input_size[-1] * 1
                )
            ]
            
            # compute the output throughput
            self.output_pixels_per_cycle = (throughput_dimension_x, throughput_dimension_y, 1)

            # calculate the delay for one compute batch
            self.delay = kernel_size[0] * kernel_size[1] * 1
        elif op_type == "FC":
            self.input_pixels_per_cycle = [input_size]
            
            # compute the output throughput
            self.output_pixels_per_cycle = output_size

            fc_mac_cnt = input_size[0] * output_size[0]
            # calculate the delay for one compute batch
            self.delay = int(input_size[0] * output_size[0] / self.size_dimension[0])

        else:
            raise Exception("Unsupported op type when configuring throughput")

        if ENABLE_DEBUG:
            print(
                "[SIMDProcessor] input throughput: ", self.input_pixels_per_cycle,
                "output throughput: ", self.output_pixels_per_cycle,
                "compute delay: ", self.delay 
            )

    # set the input hw units, the final input hw units is a list,
    # we assume multiple hw units as input
    def _set_input_hw_unit(self, sw_stage, hw_unit):
        if sw_stage not in self.input_hw_units:
            self.input_hw_units[sw_stage] = [hw_unit]
        else:
            self.input_hw_units[sw_stage].append(hw_unit)

    # initialize input buffer index, so that we know where to the next data
    # the buffer index will be indexed using (source hw unit, sw stage)
    def _init_input_buffer_index(self, src_hw_unit, sw_stage, buffer_size):
        self.input_index_list[src_hw_unit, sw_stage] = []
        for i in buffer_size:
            self.input_index_list[src_hw_unit, sw_stage].append(0)

    # get/set input buffer index
    def _get_input_buffer_index(self, src_hw_unit, sw_stage):
        return self.input_index_list[src_hw_unit, sw_stage]

    def _set_input_buffer_index(self, src_hw_unit, sw_stage, input_buffer_index):
        self.input_index_list[src_hw_unit, sw_stage] = input_buffer_index

    # initial output buffer index, here only sw stage is used as index,
    # because we consider only one output buffer
    def _init_output_buffer_index(self, sw_stage, buffer_size):
        
        self.output_pixels_per_cycle = np.ones_like(buffer_size)
        self.output_pixels_per_cycle[0] = self.size_dimension[0]

        self.output_buffer_size[sw_stage] = buffer_size
        
        self.output_index_list[sw_stage] = []
        for i in buffer_size:
            self.output_index_list[sw_stage].append(0)

    def _get_output_buffer_size(self, sw_stage):
        return self.output_buffer_size[sw_stage]

    # get/set output buffer index
    def _get_output_buffer_index(self, sw_stage):
        return self.output_index_list[sw_stage]

    def _set_output_buffer_index(self, sw_stage, output_buffer_index):
        self.output_index_list[sw_stage] = output_buffer_index

    # initialize the cycle number that needs to be elapsed before writing the output
    def _init_elapse_cycle(self):
        if self.add_init_delay:
            self.elapse_cycle = self.delay + self.initial_delay
            self.add_init_delay = False
        else:
            self.elapse_cycle = self.delay
    # process one cycle
    def _process_one_cycle(self):
        self.elapse_cycle -= 1
        self.sys_all_compute_cycle += 1
        if ENABLE_DEBUG:
            print("[PROCESS]", self.name, "just compute 1 cycle, %d cycles left" % self.elapse_cycle)

    def _start_init_delay(self):
        self.add_init_delay = True

    # check if the compute is finished, if finished, reset the elapse cycle number
    def _finish_computation(self):
        if self.elapse_cycle == 0:
            self.elapse_cycle = -1
            return True
        else:
            return False

    """
        Functions related to reading stage
    """
    # return number of read still un-read
    def _num_read_remain(self):
        total_read = self.get_total_read()

        # check if read_cnt has been initialized yet
        if self.read_cnt >= 0:
            return total_read - self.read_cnt
        else:
            return total_read

    # log num of reads happened in this reading cycle
    def _read_from_input_buffer(self, read_cnt):
        # initialize it before count
        if self.read_cnt == -1:
            self.read_cnt = 0
        self.read_cnt += read_cnt

    # check if current reading stage is finished
    def _check_read_finish(self):
        if self.read_cnt == self.get_total_read():
            # reset num_read before return
            self.read_cnt = -1
            return True
        else:
            return False

    """
        Functions related to writing stage
    """
    # return number of write still un-read
    def _num_write_remain(self):
        total_write = self.get_total_write()

        # check if write_cnt has been initialized yet
        if self.write_cnt >= 0:
            return total_write - self.write_cnt
        else:
            return total_write

    # log num of writes happened in this writing cycle
    def _write_to_output_buffer(self, write_cnt):
        # initialize it before count
        if self.write_cnt == -1:
            self.write_cnt = 0
        prev_write_cnt = self.write_cnt
        self.write_cnt += write_cnt
        return prev_write_cnt

    # check if current writing stage is finished
    def _check_write_finish(self):
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


# this function is used to convert size (H, W, C) to (X, Y, Z)
# it is hard to change the internal simulation code, this is an easy fix!
def _convert_hwc_to_xyz(name, size_list):
    new_size_list = []
    for size in size_list:
        assert len(size) == 3, "In %s, defined size needs to a size of 3!" % name
        new_size_list.append((size[1], size[0], size[2]))

    return new_size_list
