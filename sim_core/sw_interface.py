from sim_core.enum_const import Padding
from copy import deepcopy

class PixelInput(object):
    def __init__(
        self,
        size,
        name,
    ):

        self.size = size
        self.input_size = []
        self.output_size = size
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
        stride: list,
        output_size: list,
        padding: list,
    ):
        super(ProcessStage, self).__init__()
        self.name = name
        self.input_size = input_size
        self.stride = stride
        self.kernel_size = kernel_size
        self.output_size = output_size
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

        for i in range(len(self.input_size)):
            if self.input_size[i][-1] != self.kernel_size[i][-1]:
                raise Exception(
                    "The the last dimension of #%d input size and kernel size pair is mismatched!" % (i+1)
                )

        extrapolated_size = deepcopy(self.input_size)
        # first pad the input size
        for i in range(len(self.input_size)):
            if self.padding[i] == Padding.NONE: 
                # no need to change the size
                continue
            elif self.padding[i] == Padding.ZEROS:
                # change the input size 
                extrapolated_size[i] = (
                    extrapolated_size[i][0]+2*(self.kernel_size[i][0]//2),
                    extrapolated_size[i][1]+2*(self.kernel_size[i][1]//2),
                    extrapolated_size[i][2]+2*(self.kernel_size[i][2]//2)
                )
            else:
                raise Exception("Unsupported padding types.")

        for i in range(len(extrapolated_size)):
            extrapolated_size[i] = (
                (extrapolated_size[i][0] - (self.kernel_size[i][0] - self.stride[i][0])) // self.stride[i][0],
                (extrapolated_size[i][1] - (self.kernel_size[i][1] - self.stride[i][1])) // self.stride[i][1],
                (extrapolated_size[i][2] - (self.kernel_size[i][2] - self.stride[i][2])) // self.stride[i][2]
            )
            if extrapolated_size[i] != self.output_size:
                raise Exception(
                    "Size doesn't match, output size[%d] should be: (%d, %d, %d), but is (%d, %d, %d)" % \
                    (
                        i, extrapolated_size[i][0], extrapolated_size[i][1], extrapolated_size[i][2],
                        self.output_size[0], self.output_size[1], self.output_size[2]
                    )
                )


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
    ):
        super(DNNProcessStage, self).__init__()
        self.name = name
        self.op_type = op_type 
        self.input_size = [ifmap_size]
        self.ifmap_size = ifmap_size
        self.kernel_size = [kernel_size]
        self.stride = [(stride, stride, 1)]
        self.input_stages = []
        self.input_reuse = [(1, 1, 1)]
        self.output_stages = []
        self.ready_board = {}
        self.needs_flatten = False

        if op_type == "Conv2D":
            self.output_size = (
                int(self.ifmap_size[0]/stride), 
                int(self.ifmap_size[1]/stride), 
                int(self.kernel_size[0][-1])
            )
        elif op_type == "DWConv2D":
            self.output_size = (
                int(self.ifmap_size[0]/stride), 
                int(self.ifmap_size[1]/stride), 
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
