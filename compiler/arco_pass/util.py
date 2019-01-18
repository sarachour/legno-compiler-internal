import chip.props as prop
import itertools
import chip.abs as acirc

def enumerate_tree(block,n,max_blocks=None,
                   permute_input=False,prop=prop.CURRENT):
    nels = len(block.by_signal(prop,block.inputs)) if permute_input \
       else len(block.by_signal(prop,block.outputs))

    def compute_max_depth(n,n_ports):
        if n <= n_ports:
            return 1
        else:
            return 1+\
                compute_max_depth(n-(n_ports-1),n_ports)

    def count_free(levels):
        cnt = 0
        for idx in range(0,len(levels)):
            if idx == len(levels)-1:
                cnt += levels[idx]*nels

            else:
                cnt += levels[idx]*nels-levels[idx+1]

        return cnt

    levels = [1]
    max_depth = compute_max_depth(n,nels)
    choices = []
    for depth in range(0,max_depth):
        max_nodes = nels**depth
        choices.append(range(1,max_nodes+1))

    for depth in range(0,max_depth):
        for counts in itertools.product(*choices[0:depth+1]):
            if not max_blocks is None \
               and sum(counts) > max_blocks:
                continue

            free_ports = count_free(counts)
            if free_ports >= n + nels or free_ports < n:
                continue

            yield counts

def build_tree_from_levels(board,levels,block,
                           input_tree=False,
                           mode='?',
                           prop=None):
    blocks = []
    free_ports = {}

    par_ports = block.by_signal(prop,block.outputs) if input_tree \
       else block.by_signal(prop,block.inputs)

    assert(len(par_ports) == 1)
    par_port = par_ports[0]

    child_ports = block.by_signal(prop,block.inputs) if input_tree \
                  else block.by_signal(prop,block.outputs)

    # build all the nodes for each level, and all of the inputs, outputs
    nodes = {}
    parents = {}
    children = {}
    for level_idx,n_nodes in enumerate(levels):
        nodes[level_idx] = []
        parents[level_idx] = []
        children[level_idx] = []
        for idx in range(0,n_nodes):
            node = acirc.ANode.make_node(board,block.name)
            node.config.set_comp_mode(mode)
            nodes[level_idx].append(node)
            parents[level_idx].append((node,par_port))

            for port in child_ports:
                children[level_idx].append((node,port))

    # connect nodes across levels
    for level_idx,n_nodes in enumerate(levels):
        if level_idx == 0:
            free_ports[level_idx] = children[level_idx]
        else:
            offset = 0;
            last_level_idx = level_idx - 1
            for par_node in nodes[last_level_idx]:
                ch_node,ch_port = children[level_idx][offset]
                if input_tree:
                    acirc.ANode.connect(
                        par_node,par_port,
                        ch_node,ch_port
                    )
                else:
                    acirc.ANode.connect(
                        ch_node,ch_port,
                        par_node,par_port
                    )
                offset += 1

            free_ports[level_idx] = children[level_idx][offset:]


    return free_ports,nodes[len(levels)-1][0],par_port


def input_level_combos(level_inputs,sources):
    input_ports = []
    for level,inputs in level_inputs.items():
        input_ports += inputs

    for combo in itertools.permutations(input_ports,len(sources)):
        assigns = list(zip(combo,sources))
        yield assigns



def validate_fragment(frag):
    def test_inputs(inps,connected=True):
         for inp in inps:
            if frag.get_input_conn(inp) is None and connected:
                raise Exception("\n%s\n<<input %s not connected>>" % \
                                (frag.to_str(),inp))
            elif not frag.get_input_conn(inp) is None and not connected:
                raise Exception("\n%s\n<<input %s connected>>" % \
                                (frag.to_str(),inp))

         return True

    if isinstance(frag, acirc.ABlockInst):
        if frag.block.name == 'multiplier':
           if frag.config.comp_mode == 'vga':
               test_inputs(['in0'])
           else:
               test_inputs(['in0','in1'])
               test_inputs(['coeff'],connected=False)
        elif frag.block.name == 'tile_dac':
            test_inputs(['in'],connected=False)
        else:
            raise Exception("unimplemented block: %s" % frag.block.name)

        for subn in frag.subnodes():
            validate_fragment(subn)

    elif isinstance(frag,acirc.AConn):
        snode,sport = frag.source
        validate_fragment(snode)

    elif isinstance(frag,acirc.AInput):
        return

    elif isinstance(frag,acirc.AJoin):
        assert(len(list(frag.subnodes())) > 0)
        for subn in frag.subnodes():
            validate_fragment(subn)

    else:
        raise Exception("unimplemented:validate %s" % frag)

def sample(optmap):
    choice = {}
    for var_name,choices in optmap.items():
        idx = random.randint(0,len(choices)-1)
        choice[var_name] = idx

    return choice
