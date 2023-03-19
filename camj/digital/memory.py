import numpy as np

# import local module
from camj.general.enum import ProcessorLocation, ProcessDomain
from camj.general.flags import *

'''
This is the base class for digital storage memory.
IMPORTANT: Don't use this class directly, use the derived class instead!

A very important attribute in DigitalStorage class is reserved_buffer.
Reserved_buffer is used to find the consumer-producer connections between
two hardware compute units. It is important to find whether the data dependency
is ready or not.

'''
class DigitalStorage(object):
    """Base class for digital storage"""
    def __init__(
        self, 
        name: str,
        access_units: list, # a list of hardware units that access this storage
        location=ProcessorLocation.INVALID,  # location of this unit
    ):
        super(DigitalStorage, self).__init__()
        self.name = name
        self.access_units = access_units
        assert location != ProcessorLocation.INVALID, \
            "the storage location needs to be initialized."
        self.location = location
        # important to initialize the reserved_buffer to empty dict.
        self.reserved_buffer = {}

    '''
        This function used to reserve the buffer to store the output results.
        It requires two HW units and one SW stages, these three are required to 
        allocate a buffer for a particular SW compute stage.
        To index to a right buffer, use a tuple (source_HW_unit, SW_stage).
            * source_HW_unit: is the producer HW unit in that compute stage.
            * SW_stage: is the SW stage that currently computes.
            SW_stage: 
            e.g. [source_HW_unit] -- buffer --> [destination_HW_unit]
    '''
    def reserve_buffer(self, src_hw_unit, dst_hw_unit, sw_stage, buffer_size, virtual_size):
        # allocate a buffer to store the intermediate result.
        if not (src_hw_unit, sw_stage) in self.reserved_buffer:
            # (src_hw_unit, sw_stage) is the dict key.
            self.reserved_buffer[src_hw_unit, sw_stage] = np.ones(virtual_size)
            self.reserved_buffer[src_hw_unit, sw_stage][:buffer_size[0], :buffer_size[1], :buffer_size[2]] = 0

        # initialize the index for both src_hw_unit (producer) and dst_hw_unit (consumer)
        # so that both can find where they have read/written for this sw_stage.
        src_hw_unit.init_output_buffer_index(sw_stage, buffer_size)
        dst_hw_unit.init_input_buffer_index(src_hw_unit, sw_stage, virtual_size)
        
    '''
        This function is similar to function, reserve_buffer. However, 
        this function used to reserve the buffer to store the final result. 
        only the source sw stage is required. No need for stage sw stage.
    '''
    def reserve_solo_buffer(self, src_hw_unit, sw_stage, buffer_size):
        if not (src_hw_unit, sw_stage) in self.reserved_buffer:
            self.reserved_buffer[src_hw_unit, sw_stage] = np.zeros(buffer_size)

        src_hw_unit.init_output_buffer_index(sw_stage, buffer_size)

    def add_access_unit(self, unit_name):
        self.access_units.append(unit_name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class LineBuffer(DigitalStorage):
    """
        Line buffer class, extended from DigitalStorage base class
        size (a, b) will define the number of rows and the size of each row in line buffer,
        the number of row also defines the number of write port.
        Here, a is the number of read port, the number of write port is always 1.
    """
    def __init__(
        self,
        name: str,
        size: tuple,        # (a, b) a: # of row, b: the size of each row, unit in pixel
        location: int,      # location of this unit
        write_energy_per_word: int,  # energy cost for each write
        read_energy_per_word: int,   # energy cost for each read
        pixels_per_write_word: int,      # the length of each write. Unit in pixel
        pixels_per_read_word: int,       # the length of one read. Unit is pixel
    ):
        super(LineBuffer, self).__init__(
            name = name,
            access_units = [],
            location = location
        )
        self.stored_data = 0
        self.size = (size[0], size[1]) # size in unit of pixel
        self.capacity = size[0] * size[1]
        self.write_energy_per_word = write_energy_per_word
        self.read_energy_per_word = read_energy_per_word
        self.pixels_per_write_word = pixels_per_write_word
        self.pixels_per_read_word = pixels_per_read_word
        self.total_write_cnt = 0
        self.total_read_cnt = 0

    """
        Check if there is enough space to store the data
    """
    def have_space_to_write(self, num_write):

        if self.stored_data + num_write > self.capacity:
            return False
        else:
            return True

    """
        This function writes num of writes to the line buffer,
        use function 'have_space_to_write' before calling this function
    """
    def write_data(self, num_write):
        assert self.stored_data + num_write <= self.capacity, \
            "This line buffer '%s' exceeds its own capacity!" % self.name

        self.stored_data += num_write
        self.total_write_cnt += num_write
        if ENABLE_DEBUG:
            print("[MEMORY] WRITE", self.name, "has %d of data" % self.stored_data)

    """
        Check if there is enough data can be read from line buffer
    """
    def have_data_read(self, num_read):
        if num_read > self.stored_data:
            return False
        else:
            return True

    """
        This function record the number of reads from the FIFO,
        it also pops the number of no-longer-use data out of FIFO.
        In FIFO, every time you read a number, that number is no longer useful.
    """
    def read_data(self, num_read):
        assert num_read <= self.stored_data, \
            "Line buffer '%s' the number of data read is greater than stored data!" % self.name

        self.stored_data -= self.pixels_per_write_word
        self.total_read_cnt += num_read
        if ENABLE_DEBUG:
            print("[MEMORY] READ", self.name, "has %d of data" % self.stored_data)

    """
        Calculate the total memory access energy
    """
    def total_memory_access_energy(self):
        # number of write access = number of written pixel / write word length
        total_write_access = self.total_write_cnt / self.pixels_per_write_word
        # number of read access = number of read pixel / read word length
        total_read_access = self.total_read_cnt / self.pixels_per_read_word
        # total write memory energy
        write_mem_energy = self.write_energy_per_word * total_write_access
        # total read memory energy
        read_mem_energy = self.read_energy_per_word * total_read_access
        # return total memory energy
        return write_mem_energy + read_mem_energy

class FIFO(DigitalStorage):
    """
        FIFO defines only one read port and one write port,
        only one HW unit is able to read from this FIFO
        and only one HW unit is able to write to this FIFO.
    """
    def __init__(
        self,
        name: str,          # user-defined name
        size: int,          # size of FIFO struct, unit in pixel
        location: int,      # location of this unit
        write_energy_per_word: int,  # energy cost for each write
        read_energy_per_word: int,   # energy cost for each read
        pixels_per_write_word: int,      # the size of each write, unit in pixel
        pixels_per_read_word: int,       # the size of each read, unit in pixel
    ):
        super(FIFO, self).__init__(
            name = name,
            access_units = [],
            location = location
        )
        self.stored_data = 0
        self.capacity = size
        self.size = size
        self.write_energy_per_word = write_energy_per_word
        self.read_energy_per_word = read_energy_per_word
        self.pixels_per_write_word = pixels_per_write_word
        self.pixels_per_read_word = pixels_per_read_word
        self.total_write_cnt = 0
        self.total_read_cnt = 0

    """
        Check if there is enough space to store the data
    """
    def have_space_to_write(self, num_write):
        if self.stored_data + num_write > self.capacity:
            return False
        else:
            return True

    """
        This function writes num of writes to this FIFO,
        use function 'have_space_to_write' before calling this function
        num_write unit is in pixel
    """
    def write_data(self, num_write):
        assert self.stored_data + num_write <= self.capacity, \
            "FIFO '%s' exceeds its own capacity! abort!" % self.name

        self.stored_data += num_write
        self.total_write_cnt += num_write
        if ENABLE_DEBUG:
            print("[MEMORY] WRITE", self.name, "has %d of data" % self.stored_data)

    """
        Check if there is enough data can be read from FIFO
    """
    def have_data_read(self, num_read):
        if num_read > self.stored_data:
            return False
        else:
            return True

    """
        This function record the number of reads from the FIFO,
        it also pops the number of no-longer-use data out of FIFO.
        In FIFO, every time you read a number, that number is no longer useful.
    """
    def read_data(self, num_read):
        assert num_read <= self.stored_data, \
            "FIFO '%s': the number of read from FIFO is greater than stored data!" % self.name

        self.stored_data -= num_read
        self.total_read_cnt += num_read
        if ENABLE_DEBUG:
            print("[MEMORY] READ", self.name, "has %d of data" % self.stored_data)

    """
        Calculate the total memory access energy
    """
    def total_memory_access_energy(self):
        # number of write access = number of written pixel / write word length
        total_write_access = self.total_write_cnt / self.pixels_per_write_word
        # number of read access = number of read pixel / read word length
        total_read_access = self.total_read_cnt / self.pixels_per_read_word
        # total write memory energy
        write_mem_energy = self.write_energy_per_word * total_write_access
        # total read memory energy
        read_mem_energy = self.read_energy_per_word * total_read_access
        # return total memory energy
        return write_mem_energy + read_mem_energy


class DoubleBuffer(DigitalStorage):
    """docstring for DoubleBuffer"""
    def __init__(
        self, 
        name: str,
        size: tuple,        # This defines one buffer size. 
                            # (a, b, c) a: # of sram, b: # of bank, c: the size of each bank
        write_energy_per_word: int,  # energy cost for each write
        read_energy_per_word: int,   # energy cost for each read
        pixels_per_write_word: int,      # the length of each write. Unit in pixel
        pixels_per_read_word: int,       # the length of one read. Unit is pixel
        location: int,          # location of this unit
    ):
        super(DoubleBuffer, self).__init__(
            name = name,
            access_units = [],
            location = location
        )
        self.stored_data = 0
        self.size = size
        self.write_energy_per_word = write_energy_per_word
        self.read_energy_per_word = read_energy_per_word
        self.pixels_per_write_word = pixels_per_write_word
        self.pixels_per_read_word = pixels_per_read_word
        self.total_write_cnt = 0
        self.total_read_cnt = 0

    """
        Check if there is enough space to store the data
    """
    def have_space_to_write(self, num_write):
        return True

    """
        This function writes num of writes to the line buffer,
        use function 'have_space_to_write' before calling this function
    """
    def write_data(self, num_write):
        self.stored_data += num_write
        self.total_write_cnt += num_write

    """
        Check if there is enough data can be read from line buffer
    """
    def have_data_read(self, num_read):
        if self.stored_data > 0:
            return True
        else:
            return False

    """
        This function record the number of reads from the double buffer
    """
    def read_data(self, num_read):
        self.stored_data -= num_read
        self.total_read_cnt += num_read

    """
        Calculate the total memory access energy
    """
    def total_memory_access_energy(self):
        # number of write access = number of written pixel / write word length
        total_write_access = self.total_write_cnt / self.pixels_per_write_word
        # number of read access = number of read pixel / read word length
        total_read_access = self.total_read_cnt / self.pixels_per_read_word
        # total write memory energy
        write_mem_energy = self.write_energy_per_word * total_write_access
        # total read memory energy
        read_mem_energy = self.read_energy_per_word * total_read_access
        # return total memory energy
        return write_mem_energy + read_mem_energy

