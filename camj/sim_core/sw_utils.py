

def find_src_stages(sw_stage_list):

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

def find_dst_stages(sw_stage_list):

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

def set_output_stages(sw_stage_list):
    for sw_stage in sw_stage_list:
        for in_stage in sw_stage.input_stages:
            in_stage.set_output_stage(sw_stage)

def build_ready_board(sw_stage_list):
    for sw_stage in sw_stage_list:
        for in_stage in sw_stage.input_stages:
            sw_stage.construct_ready_board(in_stage)

def build_sw_graph(sw_stage_list):

    set_output_stages(sw_stage_list)
    build_ready_board(sw_stage_list)

    # output data dependency
    for sw_stage in sw_stage_list:
        print(sw_stage, "output stages:", sw_stage.output_stages)

    root_src_stage = find_src_stages(sw_stage_list)
    root_dst_stage = find_dst_stages(sw_stage_list)

    print("Root source: ", root_src_stage)
    print("Final target: ", root_dst_stage)
    
    return

