from copy import deepcopy

class PixelInput(object):
    """Pixel Input Interface

    This class is used to define pixel input stage in software pipeline.

    Args:
        name (str): define a name for this ``PixelInput`` class.
        size (tuple): define the input size of this pixel input, the format is ``(H, W, C)``.

    Examples:
        To initialized a ``PixelInput`` instance.

        >>> PixelInput("Input", (128, 128, 1))

        This will initialize a ``128x128x1`` pixel input.
    """
    def __init__(
        self,
        name,
        size, # (H, W, C)
        
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
        """Specify the output stage for this ``PixelInput``.

        Specify the output stage for this ``PixelInput``. This function can be called multiple
        times to this ``PixelInput`` has multiple consumers.

        Args:
            stage: output stage of this ``PixelInput`` instance.

        Examples:
            >>> pixel_stage.set_output_stage(resize_stage)

        """
        self.output_stages.append(stage)

    def _check_ready_board(self):
        return True

class WeightInput(object):
    """Weight Input Interface

    This class is used to define some input stages other than pixel inputs. For instance, users
    can use this stage to define a weight input in convolution.

    Args:
        name (str): define a name for this ``PixelInput`` class.
        size (tuple): define the input size of this pixel input, the format is ``(H, W, C)``.

    Examples:
        To initialized a ``WeightInput`` instance.

        >>> WeightInput("Input", (3, 3, 1))

        This will initialize a ``3x3x1`` weight input which can be used in a convolution.

    """
    def __init__(
        self,
        name,
        size, # (H, W, C)
    ):
        assert len(size) == 3, "WeightInput size should be a tuple of length 3!"

        self.size = (size[1], size[0], size[2]) # covert to internal representation (x, y, z)
        self.kernel_size = self.size
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
        """Specify the output stage for this ``WeightInput``.

        Specify the output stage for this ``PixelInput``. This function can be called multiple
        times to this ``WeightInput`` has multiple consumers.

        Args:
            stage: output stage of this ``WeightInput`` instance.

        Examples:
            >>> weight_input.set_output_stage(conv_stage)

        """
        self.output_stages.append(stage)

    def _check_ready_board(self):
        return True


class ProcessStage(object):
    """A Class to Define General Processing Stages in Software

    This class is used to define a general processing stages in software pipeline.
    The software stage needs to fulfill one requirement: this processing stage is
    a stencil operation.

    Args:
        name (str): the name of this software stage.
        input_size (list): define the input shape of this processing stage. The input size 
            should be in a list of tuples.
        kernel_size (list): define the operation kernel shape of this processing stage. The
            kernel size should be a list of ``tuple``. Each input can only has one kernel shape
            operating on it. See examples below.
        num_kernels (list): define the number of kernels for each kernel in ``kernel_size`` list.
            This parameter should be a list of ``int``.
        stride (list): define the processing stride for each kernel. This parameter should be
            a list of ``tuple``.
        padding (list): define whether applying paddings to each kernel operation. This parameter
            should be a list of ``int``.

    Examples:
        To define a convolution with two (3x3x1) weights, stride of 2 and no padding. 

        >>> ProcessStage(
            name = "Conv",
            input_size = [(128, 128, 1)],
            kernel_size = [(3, 3, 1)],
            num_kernels = [2],
            stride = [(2, 2, 1)],
            padding = [False]
        )

        To define a stencil operation with two inputs, ``128x128x1`` and ``64x64x1``, each input
        is operated with different kernel sizes ``2x2x1`` and ``1x1x1``, assuming no padding.

        >>> ProcessStage(
            name = "Conv",
            input_size = [(128, 128, 1), (64, 64, 1)],
            kernel_size = [(2, 2, 1), (1, 1, 1)],
            num_kernels = [1, 1],
            stride = [(2, 2, 1), (1, 1, 1)],
            padding = [False, False]
        )

        Here, each kernel operates on its own input. The first ``128x128x1`` input operates with 
        ``2x2x1`` kernel and the second ``64x64x1`` input operates with ``1x1x1`` kernel. Make 
        sure both inputs result in the same output, otherwise, an error will occur.
    """
    def __init__(
        self, 
        name: str,
        input_size: list,
        kernel_size: list,
        num_kernels: list,
        stride: list,
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
        self._check_consistency()

    def set_input_stage(self, stage):
        """Specify the input stage for this ``ProcessStage``.

        Specify the input stage for this ``ProcessStage``. This function can be called multiple
        times to this ``ProcessStage`` has multiple producers.

        Args:
            stage: input stage of this ``ProcessStage`` instance.
        """
        self.input_stages.append(stage)

    def set_output_stage(self, stage):
        """Specify the output stage for this ``ProcessStage``.

        Specify the output stage for this ``ProcessStage``. This function can be called multiple
        times to this ``ProcessStage`` has multiple consumers.

        Args:
            stage: output stage of this ``ProcessStage`` instance.
        """
        self.output_stages.append(stage)

    def _check_consistency(self):
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

    def _is_parent_of(self, process_stage):

        if process_stage in self.input_stages:
            return True
        else:
            return False

    def _is_child_process_of(self, process_stage):

        if process_stage in self.input_stages:
            return True
        else:
            return False

    def _construct_ready_board(self, stage):
        self.ready_board[stage] = False

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name        

class DNNProcessStage(object):
    """A Class to Define DNN Processing Stage

    Args:
        name (str): the name of this software stage.
        op_type (str): define the DNN operation type. Now we support ``Conv2D``, ``DWConv2`` and ``FC``.
        ifmap_size (list): define the input shape of this processing stage. The input size 
            should be in a list of ``int``. The order should be ``[H, W, C_in]``.
        kernel_size (list): define the operation kernel shape of this processing stage. The
            kernel size should be a list of ``int``. The order should be ``[H, W, C_in, C_out]``.
        stride (int): define the processing stride of this DNN operation.
        padding (bool): define whether applying paddings to DNN operation.

    Examples:
        To define convolution with input of ``128x128x3`` and kernel shape of ``3x3x3x16``.

        >>> DNNProcessStage(
            name = "DNN-Conv",
            op_type = "Conv2D",
            ifmap_size = [128, 128, 3],
            kernel_size = [3, 3, 3, 16],
            stride = 2,
            padding = True
        )

    """
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
        """Set flatten flag when operating from convolution to FC layer."""
        self.needs_flatten = True

    def set_input_stage(self, stage):
        """Specify the input stage for this ``DNNProcessStage``.

        Specify the input stage for this ``DNNProcessStage``. This function can be called multiple
        times to this ``DNNProcessStage`` has multiple producers.

        Args:
            stage: input stage of this ``ProcessStage`` instance.
        """
        self.input_stages.append(stage)

    def set_output_stage(self, stage):
        """Specify the output stage for this ``DNNProcessStage``.

        Specify the output stage for this ``DNNProcessStage``. This function can be called multiple
        times to this ``DNNProcessStage`` has multiple consumers.

        Args:
            stage: output stage of this ``DNNProcessStage`` instance.
        """
        self.output_stages.append(stage)

    def _is_parent_of(self, process_stage):

        if process_stage in self.input_stages:
            return True
        else:
            return False

    def _is_child_process_of(self, process_stage):

        if process_stage in self.input_stages:
            return True
        else:
            return False

    def _construct_ready_board(self, stage):
        self.ready_board[stage] = False

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