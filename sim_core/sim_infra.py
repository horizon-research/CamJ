
'''
    This class is used to record which HW compute unit is currently occupied by a SW stage.
    Basic assumption is that when a SW stage occupies a HW unit, it won't release the HW unit
    until it finishes all its computation.

    How to ReservationBoard class:
    * check_reservation: to check whether a HW unit is being occupied.
    * reserve_hw_unit: to reserve the HW unit. 
    * reserve_by: to check if a HW unit is reserved by a certain SW stage.
    * release_hw_unit: to release the HW unit for other SW stage use.
'''
class ReservationBoard(object):
    """docstring for ReservationBoard"""
    def __init__(self, hw_compute_units):
        super(ReservationBoard, self).__init__()
        self.occupation_board = {}
        self.reservation_board = {}
        for hw_unit in hw_compute_units:
            self.reservation_board[hw_unit] = False

    def check_reservation(self, hw_unit):
        if hw_unit in self.reservation_board:
            return self.reservation_board[hw_unit]
        else:
            raise Exception("%s is not in the reservation board" % hw_unit.name)
        
    def reserve_hw_unit(self, sw_stage, hw_unit):
        if self.reservation_board[hw_unit]:
            raise Exception("%s has already been reserved." % hw_unit.name)
        else:
            self.reservation_board[hw_unit] = True
            self.occupation_board[hw_unit] = sw_stage

    def reserve_by(self, sw_stage, hw_unit):
        # check if the hw_unit is reserved or not
        if not self.reservation_board[hw_unit]:
            return False
        # check if the occupied sw stage is the query sw stage
        if self.occupation_board[hw_unit] == sw_stage:
            return True
        else:
            return False

    def release_hw_unit(self, sw_stage, hw_unit):
        self.reservation_board[hw_unit] = False
        self.occupation_board.pop(hw_unit, None)


class BufferMonitor(object):
    """docstring for BufferMonitor"""
    def __init__(self, buffer_list):
        super(BufferMonitor, self).__init__()
        self.buffer_list = buffer_list
        # store the R/W port config
        self.total_read_port = {}
        self.total_write_port = {}
        # initialize the R/W port status
        self.occupied_read_port = {}
        self.occupied_write_port = {}
        for buffer in buffer_list:
            self.total_read_port[buffer] = buffer.read_port
            self.total_write_port[buffer] = buffer.write_port
            self.occupied_read_port[buffer] = 0
            self.occupied_write_port[buffer] = 0

    # check if there is any available read port for this buffer
    def check_buffer_available_read_port(self, buffer):
        if buffer is None:
            return True

        assert self.occupied_read_port[buffer] <= self.total_read_port[buffer], \
            "occupied_read_port cannot be greater than total_read_port"

        # occupied read port equals to total read port, then, no available read port
        if self.occupied_read_port[buffer] == self.total_read_port[buffer]:
            return False
        else:
            return True

    # request a certain number of read port, after request, it increments occupied_read_port
    #   * buffer: buffer class
    #   * num_port: number of read ports are needed
    # return:
    #   it returns number of ports that can be satisfied
    #   this number <= num_port
    def request_read_port(self, buffer, num_port):
        # check if the request is zero. if zero, return directly
        if num_port == 0:
            return 0
        avail_port = self.total_read_port[buffer] - self.occupied_read_port[buffer]
        self.occupied_read_port[buffer] += avail_port
        if avail_port > num_port:
            return num_port
        else:
            return avail_port

    # check if there is any available write port for this buffer
    def check_buffer_available_write_port(self, buffer):
        assert self.occupied_write_port[buffer] <= self.total_write_port[buffer], \
            "occupied_write_port cannot be greater than total_write_port"

        # occupied write port equals to total write port, then, no available write port
        if self.occupied_write_port[buffer] == self.total_write_port[buffer]:
            return False
        else:
            return True

    # request a certain number of write port, after request, it increments occupied_write_port
    #   * buffer: buffer class
    #   * num_port: number of write ports are needed
    # return:
    #   it returns number of ports that can be satisfied
    #   this number <= num_port
    def request_write_port(self, buffer, num_port):
        avail_port = self.total_write_port[buffer] - self.occupied_write_port[buffer]
        self.occupied_write_port[buffer] += avail_port
        if avail_port > num_port:
            return num_port
        else:
            return avail_port

    # refresh the port number after each cycle
    def refresh_port_status(self):
        for k in self.occupied_read_port.keys():
            self.occupied_read_port[k] = 0
        for k in self.occupied_write_port.keys():
            self.occupied_write_port[k] = 0





        
