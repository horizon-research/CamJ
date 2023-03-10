from copy import deepcopy

class PixelInput(object):
    def __init__(
        self,
        size, # (H, W, C)
        name,
    ):
        assert len(size) == 3, "PixelInput size should be a tuple of length 3!"

        self.size = (size[1], size[0], size[2]) # covert to internal representation (x, y, z)
        self.input_size = []
        self.output_size = (size[1], size[0], size[2]) # covert to internal representation (x, y, z)
        self.input_stages = []
        self.name = name
        self.output_stages = []
        self.ready_board = {}

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def set_output_stage(self, stage):
        self.output_stages.append(stage)

    def check_ready_board(self):
        return True

class WeightInput(object):
    def __init__(
        self,
        size, # (H, W, C)
        name,
    ):
        assert len(size) == 3, "WeightInput size should be a tuple of length 3!"

        self.size = (size[1], size[0], size[2]) # covert to internal representation (x, y, z)
        self.input_size = []
        self.output_size = (size[1], size[0], size[2]) # covert to internal representation (x, y, z)
        self.input_stages = []
        self.name = name
        self.output_stages = []
        self.ready_board = {}

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def set_output_stage(self, stage):
        self.output_stages.append(stage)

    def check_ready_board(self):
        return True


class ProcessStage(object):
    """docstring for ProcessStage"""
    def __init__(
        self, 
        name: str,
        input_size: list,
        kernel_size: list,
        num_kernels: list,
        stride: list,
        # output_size: list,
        padding: list,
    ):
        super(ProcessStage, self).__init__()
        self.name = name
        self.input_size = _convert_hwc_to_xyz(name, input_size) # covert to internal representation (x, y, z)
        self.kernel_size = _convert_hwc_to_xyz(name, kernel_size) # covert to internal representation (x, y, z)
        self.stride = _convert_hwc_to_xyz(name, stride) # covert to internal representation (x, y, z)
        self.num_kernels = num_kernels
        # self.output_size = (output_size[1], output_size[0], output_size[2]) # covert to internal representation (x, y, z)
        self.input_stages = []
        self.output_stages = []
        self.ready_board = {}
        self.padding = padding
        self.check_consistency()

    def check_consistency(self):
        if len(self.input_size) != len(self.kernel_size):
            raise Exception(
                "ProcessStage '%s' input_size length (%d) is not the same as kernel_size length (%d)" % (
                    self.name,
                    len(self.input_size),
                    len(self.kernel_size)
                )
            )
        if len(self.input_size) != len(self.stride):
            raise Exception(
                "ProcessStage '%s' input_size length (%d) is not the same as stride length (%d)" % (
                    self.name,
                    len(self.input_size),
                    len(self.stride)
                )
            )
        if len(self.input_size) != len(self.padding):
            raise Exception(
                "ProcessStage '%s' input_size length (%d) is not the same as padding length (%d)" % (
                    self.name,
                    len(self.input_size),
                    len(self.padding)
                )
            )

        extrapolated_size = deepcopy(self.input_size)
        # first pad the input size
        for i in range(len(self.input_size)):
            if self.padding[i]:
                # change the input size 
                extrapolated_size[i] = (
                    extrapolated_size[i][0]+2*(self.kernel_size[i][0]//2),
                    extrapolated_size[i][1]+2*(self.kernel_size[i][1]//2),
                    extrapolated_size[i][2]+2*(self.kernel_size[i][2]//2)
                )

        # calculate output size
        for i in range(len(extrapolated_size)):
            extrapolated_size[i] = (
                (extrapolated_size[i][0] - (self.kernel_size[i][0] - self.stride[i][0])) // self.stride[i][0],
                (extrapolated_size[i][1] - (self.kernel_size[i][1] - self.stride[i][1])) // self.stride[i][1],
                (extrapolated_size[i][2] - (self.kernel_size[i][2] - self.stride[i][2])) // self.stride[i][2] * self.num_kernels[i]
            )

        # pick any element in extrapolatied_size is output size
        self.output_size = extrapolated_size[0]

    def set_input_stage(self, stage):
        self.input_stages.append(stage)

    def set_output_stage(self, stage):
        self.output_stages.append(stage)

    def is_parent_of(self, process_stage):

        if process_stage in self.input_stages:
            return True
        else:
            return False

    def is_child_process_of(self, process_stage):

        if process_stage in self.input_stages:
            return True
        else:
            return False

    def construct_ready_board(self, stage):
        self.ready_board[stage] = False

    def set_ready_board(self, stage):
        self.ready_board[stage] = True

    def check_ready_board(self):
        for k in self.ready_board:
            if self.ready_board[k] == False:
                return False

        return True

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name        

class DNNProcessStage(object):
    """docstring for DNNProcessStage"""
    def __init__(
        self,
        name: str,
        op_type: str,
        ifmap_size: list,
        kernel_size: list,
        stride: int,
        padding = True
    ):
        super(DNNProcessStage, self).__init__()
        self.name = name
        self.op_type = op_type

        assert len(ifmap_size) == 3, "In '%s', ifmap should be a size of 3 (H, W, C)" % name
        assert len(kernel_size) == 4, "In '%s', kernel_size should be a size of 4 (H, W, C_in, C_out)" % name

        self.input_size = _convert_hwc_to_xyz(name, [ifmap_size]) # covert to internal representation (x, y, z)
        self.ifmap_size = (ifmap_size[1], ifmap_size[0], ifmap_size[2]) # covert to internal representation (x, y, z)
        self.kernel_size = [
            (
                kernel_size[1],
                kernel_size[0],
                kernel_size[2],
                kernel_size[3]
            )
        ] # covert (H, W, C_in, C_out) to internal representation (x, y, z1, z2)
        self.stride = _convert_hwc_to_xyz(name, [(stride, stride, 1)])# covert to internal representation (x, y, z)
        self.input_stages = []
        self.input_reuse = [(1, 1, 1)]
        self.output_stages = []
        self.ready_board = {}
        self.needs_flatten = False

        if op_type == "Conv2D" or op_type == "DWConv2D":
            if padding:
                self.output_size = (
                    int(self.ifmap_size[0] / stride), 
                    int(self.ifmap_size[1] / stride), 
                    int(self.kernel_size[0][-1])
                )
            else:
                self.output_size = (
                    int((self.ifmap_size[0] - self.kernel_size[0] + 1) / stride), 
                    int((self.ifmap_size[1] - self.kernel_size[1] + 1) / stride), 
                    int(self.kernel_size[0][-1])
                )
        elif op_type == "FC":
            self.output_size = (
                int(self.kernel_size[0][1]),
                1,
                1
            )
        else:
            raise Exception("Unsupported op types in class 'DNNProcessStage'.")

    def flatten(self):
        self.needs_flatten = True

    def set_input_stage(self, stage):
        self.input_stages.append(stage)

    def set_output_stage(self, stage):
        self.output_stages.append(stage)

    def is_parent_of(self, process_stage):

        if process_stage in self.input_stages:
            return True
        else:
            return False

    def is_child_process_of(self, process_stage):

        if process_stage in self.input_stages:
            return True
        else:
            return False

    def construct_ready_board(self, stage):
        self.ready_board[stage] = False

    def set_ready_board(self, stage):
        self.ready_board[stage] = True

    def check_ready_board(self):
        for k in self.ready_board:
            if self.ready_board[k] == False:
                return False

        return True

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