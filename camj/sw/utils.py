
def build_sw_graph(sw_stage_list: list):
    """Build Software Graph

    This function complete the software graph after user defines the software pipeline.
    In software pipeline definition, it only asks users to define the output stages for
    each software stage, Here, this function completes the graph by finding input stages
    for each software stage.

    Args:
        sw_stage_list (list): a list of user-defined software stages.

    """
    if len(sw_stage_list) == 0:
        return

    _set_output_stages(sw_stage_list)
    _build_ready_board(sw_stage_list)

    # output data dependency
    for sw_stage in sw_stage_list:
        print("'%s' output stages:" % sw_stage, sw_stage.output_stages)

    root_src_stage = _find_src_stages(sw_stage_list)
    root_dst_stage = _find_dst_stages(sw_stage_list)

    print("Root source: ", root_src_stage, "Final target: ", root_dst_stage)
    
    return

def _find_src_stages(sw_stage_list):

    parent_stages = []
    prev_parent_stages = []
    for sw_stage in sw_stage_list:
        prev_parent_stages.append(sw_stage)

    for i in range(len(sw_stage_list)):
        for sw_stage in prev_parent_stages:
            if len(sw_stage.input_stages) == 0:
                if sw_stage not in parent_stages:
                    parent_stages.append(sw_stage)
            else:
                for curr_parent_stage in sw_stage.input_stages:
                    if curr_parent_stage not in parent_stages:
                        if curr_parent_stage not in parent_stages:
                            parent_stages.append(curr_parent_stage)

        prev_parent_stages = []
        for stage in parent_stages:
            prev_parent_stages.append(stage)

        parent_stages = []

    return prev_parent_stages

def _find_dst_stages(sw_stage_list):

    child_stages = []

    for child_stage in  sw_stage_list:
        is_child_stage = True
        for sw_stage in sw_stage_list:
            if child_stage in sw_stage.input_stages:
                is_child_stage = False
                break

        if is_child_stage:
            child_stages.append(child_stage)

    return child_stages

def _set_output_stages(sw_stage_list):
    for sw_stage in sw_stage_list:
        for in_stage in sw_stage.input_stages:
            in_stage.set_output_stage(sw_stage)

def _build_ready_board(sw_stage_list):
    for sw_stage in sw_stage_list:
        for in_stage in sw_stage.input_stages:
            sw_stage._construct_ready_board(in_stage)


