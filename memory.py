import numpy as np

from enum_const import ProcessorLocation, ProcessDomain

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
            access_units: list,  # a list of hardware units that access this storage
            location=0: int,  # location of this unit
    ):
    super(DigitalStorage, self).__init__()
    self.name = name
    self.access_units = access_units
    assert (location > 0, "the storage location needs to be greater than 0, got: %d" % location)
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


def reserve_buffer(self, src_hw_unit, dst_hw_unit, sw_stage, buffer_size):
    # print(buffer_size)
    # allocate a buffer to store the intermediate result.
    if not (src_hw_unit, sw_stage) in self.reserved_buffer:
        # (src_hw_unit, sw_stage) is the dict key.
        self.reserved_buffer[src_hw_unit, sw_stage] = np.zeros(buffer_size)

    # initialize the index for both src_hw_unit (producer) and dst_hw_unit (consumer)
    # so that both can find where they have read/written for this sw_stage.
    src_hw_unit.init_output_buffer_index(sw_stage, buffer_size)
    dst_hw_unit.init_input_buffer_index(src_hw_unit, sw_stage, buffer_size)


'''
    This function is similar to function, eserve_buffer. However, 
    this function used to reserve the buffer to store the final result. 
    only the source sw stage is required. No need for stage sw stage.
'''


def reserve_solo_buffer(self, src_hw_unit, sw_stage, buffer_size):
    print(buffer_size)
    if not (src_hw_unit, sw_stage) in self.reserved_buffer:
        self.reserved_buffer[src_hw_unit, sw_stage] = np.zeros(buffer_size)

    src_hw_unit.init_output_buffer_index(sw_stage, buffer_size)


def __str__(self):
    return self.name


def __repr__(self):
    return self.name


class SRAM(DigitalStorage):
    """docstring for SRAM"""

    def __init__(
            self,
            name: str,
            size: tuple,  # (a, b, c) a: # of sram, b: # of bank, c: the size of each bank
            clock: int,  # clock frequency
            read_port: int,  # num of read ports
            write_port: int,  # num of write ports
            read_write_port: int,  # num of read&write ports
            write_energy: int,  # energy cost for each write
            read_energy: int,  # energy cost for each read
            access_units: list,  # a list of hardware units that access this storage
            location: int,  # location of this unit
    ):
        super(LineBuffer, self).__init__(
            name=name,
            access_units=access_units,
            location=location
        )
        self.size = size
        self.clock = clock
        self.read_port = read_port
        self.write_port = write_port
        self.read_write_port = read_write_port
        self.write_energy = write_energy
        self.read_energy = read_energy


class LineBuffer(DigitalStorage):
    """docstring for LineBuffer"""

    def __init__(
            self,
            name: str,
            size: tuple,  # (a, b) a: # of row, b: the size of each row
            hw_impl: str,  # "ff" or "sram"
            impl: str,  # "fifo" or "non-fifo" implementation
            clock: int,  # clock frequency
            read_port: int,  # num of read ports
            write_port: int,  # num of write ports
            write_energy: int,  # energy cost for each write
            read_energy: int,  # energy cost for each read
            access_units: list,  # a list of hardware units that access this storage
            location: int,  # location of this unit
    ):
        super(LineBuffer, self).__init__(
            name=name,
            access_units=access_units,
            location=location
        )
        self.size = size
        self.clock = clock
        self.impl = impl
        self.write_port = write_port
        self.read_port = read_port
        self.write_energy = write_energy
        self.read_energy = read_energy


class DRAM(DigitalStorage):
    """docstring for DRAM"""

    def __init__(
            self,
            name: str,
            size: int,
            clock: int,  # clock frequency
            read_port: int,  # num of read ports
            write_port: int,  # num of write ports
            read_write_port: int,  # num of read&write ports
            random_write_energy: int,  # energy cost for each random write
            random_read_energy: int,  # energy cost for each random read
            seq_write_energy: int,  # eneegy cost for each sequential write
            seq_read_energy: int,  # energy cost for each sequential read
            access_units: list,  # a list of hardware units that access this storage
            location: int,  # location of this unit
    ):
        super(DRAM, self).__init__(
            name=name,
            access_units=access_units,
            location=location
        )

        self.size = size
        self.clock = clock

        self.read_port = read_port
        self.write_port = write_port
        self.read_write_port = read_write_port
        self.random_write_energy = random_write_energy
        self.random_read_energy = random_read_energy
        self.seq_write_cap_per_cycle = seq_write_cap_per_cycle
        self.seq_read_cap_per_cycle = seq_read_cap_per_cycle
        self.seq_write_energy = seq_write_energy
        self.seq_read_energy = seq_read_energy


class Scratchpad(DigitalStorage):
    """docstring for Scratchpad"""

    def __init__(
            self,
            name: str,
            size: tuple,  # (a, b, c) a: # of sram, b: # of bank, c: the size of each bank
            clock: int,  # clock frequency
            read_port: int,  # num of read ports
            write_port: int,  # num of write ports
            read_write_port: int,  # num of read&write ports
            write_energy: int,  # energy cost for each write
            read_energy: int,  # energy cost for each read
            access_units: list,  # a list of hardware units that access this storage
            location: int,  # location of this unit
    ):
        super(Scratchpad, self).__init__(
            name=name,
            access_units=access_units,
            location=location
        )
        self.size = size
        self.clock = clock
        self.read_port = read_port
        self.write_port = write_port
        self.read_write_port = read_write_port
        self.write_energy = write_energy
        self.read_energy = read_energy


class RegisterFile(DigitalStorage):
    """docstring for RegisterFile"""

    def __init__(
            self,
            hw_impl: str,  # "flip-flop" or "sram"
            count: tuple,  # num of register
            clock: int,  # clock frequency
            write_energy: int,  # energy cost for each write
            read_energy: int,  # energy cost for each read
            access_units: list,  # a list of hardware units that access this storage
            location: int,  # location of this unit
    ):
        super(RegisterFile, self).__init__(
            name=name,
            access_units=access_units,
            location=location
        )
        self.hw_impl = hw_impl
        self.count = count
        self.clock = clock
        self.write_energy = write_energy
        self.read_energy = read_energy


class ShiftRegister(DigitalStorage):
    """docstring for ShiftRegister"""

    def __init__(
            self,
            hw_impl: str,  # "flip-flop" or "sram"
            count: tuple,  # num of register
            clock: int,  # clock frequency
            write_energy: int,  # energy cost for each write
            read_energy: int,  # energy cost for each read
            access_units: list,  # a list of hardware units that access this storage
            location: int,  # location of this unit
    ):
        super(ShiftRegister, self).__init__(
            name=name,
            access_units=access_units,
            location=location
        )
        self.hw_impl = hw_impl
        self.count = count
        self.clock = clock
        self.write_energy = write_energy
        self.read_energy = read_energy
