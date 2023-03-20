import numpy as np

# import local module
from camj.general.enum import ProcessorLocation, ProcessDomain
from camj.general.flags import *


class DigitalStorage(object):
    """Base class for digital storage class

    This is the base class for digital storage memory.

    IMPORTANT: Don't use this class directly, use the derived class instead!

    A very important attribute in DigitalStorage class is reserved_buffer.
    Reserved_buffer is used to find the consumer-producer connections between
    two hardware compute units. It is important to find whether the data dependency
    is ready or not.

    """
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

    def _reserve_buffer(self, src_hw_unit, dst_hw_unit, sw_stage, buffer_size, virtual_size):
        """
        This function used to reserve the buffer to store the output results.
        It requires two HW units and one SW stages, these three are required to 
        allocate a buffer for a particular SW compute stage.
        To index to a right buffer, use a tuple (source_HW_unit, SW_stage).
            * source_HW_unit: is the producer HW unit in that compute stage.
            * SW_stage: is the SW stage that currently computes.

        SW_stage: 
            [source_HW_unit] -- buffer --> [destination_HW_unit]
        """
        # allocate a buffer to store the intermediate result.
        if not (src_hw_unit, sw_stage) in self.reserved_buffer:
            # (src_hw_unit, sw_stage) is the dict key.
            self.reserved_buffer[src_hw_unit, sw_stage] = np.ones(virtual_size)
            self.reserved_buffer[src_hw_unit, sw_stage][:buffer_size[0], :buffer_size[1], :buffer_size[2]] = 0

        # initialize the index for both src_hw_unit (producer) and dst_hw_unit (consumer)
        # so that both can find where they have read/written for this sw_stage.
        src_hw_unit._init_output_buffer_index(sw_stage, buffer_size)
        dst_hw_unit._init_input_buffer_index(src_hw_unit, sw_stage, virtual_size)
        
    
    def _reserve_solo_buffer(self, src_hw_unit, sw_stage, buffer_size):
        """
        This function is similar to function, reserve_buffer. However, 
        this function used to reserve the buffer to store the final result. 
        only the source sw stage is required. No need for stage sw stage.
        """
        if not (src_hw_unit, sw_stage) in self.reserved_buffer:
            self.reserved_buffer[src_hw_unit, sw_stage] = np.zeros(buffer_size)

        src_hw_unit._init_output_buffer_index(sw_stage, buffer_size)

    def _add_access_unit(self, unit_name):
        self.access_units.append(unit_name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class LineBuffer(DigitalStorage):
    """Line Buffer, extended from DigitalStorage base class

    This class follows a specific memory access pattern. The size of this class defines
    the number of read and write per cycle. For instance, a size of ``(3, 128)`` line buffer
    can be read ``3`` pixels per cycle and can be written ``1`` pixel per cycle.

    However, this class doesn't check if per-cycle read and write surpass its capacity.
    This class does check if the number of read and write requests by consumer/producer 
    can be fulfilled or not.

    Args:
        name (str): name of this memory structure.
        size (tuple): the size of the line buffer in a shape of ``(A, B)``. ``A`` is the number
            of rows in this line buffer, ``B`` is the size of each row in unit of pixel.
        location: the location of this memory unit.
        write_energy_per_word (float): energy cost for each write
        read_energy_per_word (float): energy cost for each read
        pixels_per_write_word (int): the length of each write. Unit in pixel
        pixels_per_read_word (int): the length of one read. Unit is pixel
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

    def total_memory_access_energy(self):
        """Calculate the total memory access energy

        Returns:
            Memory Access Energy (flaot): the memory access energy in unit of pJ.
        """
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
    
    def _have_space_to_write(self, num_write):
        """
        Check if there is enough space to store the data
        """

        if self.stored_data + num_write > self.capacity:
            return False
        else:
            return True

    
    def _write_data(self, num_write):
        """
        This function writes num of writes to the line buffer,
        use function 'have_space_to_write' before calling this function
        """
        assert self.stored_data + num_write <= self.capacity, \
            "This line buffer '%s' exceeds its own capacity!" % self.name

        self.stored_data += num_write
        self.total_write_cnt += num_write
        if ENABLE_DEBUG:
            print("[MEMORY] WRITE", self.name, "has %d of data" % self.stored_data)

    
    def _have_data_read(self, num_read):
        """
        Check if there is enough data can be read from line buffer
        """
        if num_read > self.stored_data:
            return False
        else:
            return True

    
    def _read_data(self, num_read):
        """
        This function record the number of reads from the FIFO,
        it also pops the number of no-longer-use data out of FIFO.
        In FIFO, every time you read a number, that number is no longer useful.
        """
        assert num_read <= self.stored_data, \
            "Line buffer '%s' the number of data read is greater than stored data!" % self.name

        self.stored_data -= self.pixels_per_write_word
        self.total_read_cnt += num_read
        if ENABLE_DEBUG:
            print("[MEMORY] READ", self.name, "has %d of data" % self.stored_data)


class FIFO(DigitalStorage):
    """FIFO Buffer

    This class emulates the hardware behavior of FIFO. Each FIFO will have one read port
    and one write port.

    Args:
        name (str): name of this memory structure.
        size (tuple): the size of FIFO in unit of pixel.
        location: the location of this memory unit.
        write_energy_per_word (float): energy cost for each write
        read_energy_per_word (float): energy cost for each read
        pixels_per_write_word (int): the length of each write. Unit in pixel
        pixels_per_read_word (int): the length of one read. Unit is pixel
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

    def total_memory_access_energy(self):
        """Calculate the total memory access energy

        Returns:
            Memory Access Energy (flaot): the memory access energy in unit of pJ.
        """
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

    def _have_space_to_write(self, num_write):
        """
        Check if there is enough space to store the data
        """
        if self.stored_data + num_write > self.capacity:
            return False
        else:
            return True

    def _write_data(self, num_write):
        """
        This function writes num of writes to this FIFO,
        use function 'have_space_to_write' before calling this function
        num_write unit is in pixel
        """
        assert self.stored_data + num_write <= self.capacity, \
            "FIFO '%s' exceeds its own capacity! abort!" % self.name

        self.stored_data += num_write
        self.total_write_cnt += num_write
        if ENABLE_DEBUG:
            print("[MEMORY] WRITE", self.name, "has %d of data" % self.stored_data)

    def _have_data_read(self, num_read):
        """
        Check if there is enough data can be read from FIFO
        """
        if num_read > self.stored_data:
            return False
        else:
            return True

    
    def _read_data(self, num_read):
        """
        This function record the number of reads from the FIFO,
        it also pops the number of no-longer-use data out of FIFO.
        In FIFO, every time you read a number, that number is no longer useful.
        """
        assert num_read <= self.stored_data, \
            "FIFO '%s': the number of read from FIFO is greater than stored data!" % self.name

        self.stored_data -= num_read
        self.total_read_cnt += num_read
        if ENABLE_DEBUG:
            print("[MEMORY] READ", self.name, "has %d of data" % self.stored_data)


class DoubleBuffer(DigitalStorage):
    """DoubleBuffer

    This class emulates the hardware behavior of double buffer.

    Args:
        name (str): name of this memory structure.
        size (tuple): the size of double buffer in a shape of ``(A, B, C)``. 
            ``A`` is number of SRAM, ``B`` is the number of bank, 
            ``C`` is the size of each bank.
        location: the location of this memory unit.
        write_energy_per_word (float): energy cost for each write
        read_energy_per_word (float): energy cost for each read
        pixels_per_write_word (int): the length of each write. Unit in pixel
        pixels_per_read_word (int): the length of one read. Unit is pixel
    """
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

    def total_memory_access_energy(self):
        """Calculate the total memory access energy

        Returns:
            Memory Access Energy (flaot): the memory access energy in unit of pJ.
        """
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

    def _have_space_to_write(self, num_write):
        """
        Check if there is enough space to store the data
        """
        return True

    
    def _write_data(self, num_write):
        """
        This function writes num of writes to the line buffer,
        use function 'have_space_to_write' before calling this function
        """
        self.stored_data += num_write
        self.total_write_cnt += num_write

    def _have_data_read(self, num_read):
        """
        Check if there is enough data can be read from line buffer
        """
        if self.stored_data > 0:
            return True
        else:
            return False

    def _read_data(self, num_read):
        """
        This function record the number of reads from the double buffer
        """
        self.stored_data -= num_read
        self.total_read_cnt += num_read

