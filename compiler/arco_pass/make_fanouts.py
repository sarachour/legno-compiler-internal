import chip.abs as acirc
import chip.props as prop
import compiler.arco_pass.util as arco_util
from chip.config import Labels
import itertools

def copy_signal(board,node,output,n_copies,label,max_fanouts):
    sources = []
    if n_copies <= 1:
        #assert(not isinstance(node,acirc.AJoin))
        sources ={0:[(node,output)]}
        yield sources,node
        return

    fanout = board.block("fanout")
    for levels in arco_util.enumerate_tree(fanout,n_copies,
                                 max_blocks=max_fanouts,
                                 permute_input=False):
        free_ports,c_node,c_input = arco_util\
                                     .build_tree_from_levels(board,
                                                             levels,
                                                             fanout,
                                                             ['out1','out0','out2'],
                                                             'in',
                                                             input_tree=False,
                                                             mode='*',
                                                             prop=prop.CURRENT
                                     )
        for level,ports in free_ports.items():
            for port_node,port in ports:
                port_node.config.set_label(port,label,kind=Labels.OUTPUT)

        new_node,ctx = node.copy()
        acirc.ANode.connect(new_node,output,c_node,c_input)

        yield free_ports,c_node



def get_valid_modes(mode_map,scf_map):
  for mode,mode_scfs in mode_map.items():
    is_match = True
    for port,scf in scf_map.items():
      if scf != mode_scfs[port]:
        is_match = False

    if is_match:
      yield mode

def cs2s_join(board,node,outputs,stubs):
    assert(len(outputs) == 1)
    assert(len(stubs) == 1)
    output,stub = outputs[0],stubs[0]
    assert(stub.coefficient == 1.0)

def cs2s_blockinst(board,node,outputs,stubs):
    block = node.block
    config = node.config
    coeffs = {}
    for output,stub in zip(outputs,stubs):
        coeffs[output] = stub.coefficient

    scfs = dict(map(lambda mode: (mode,{}) ,block.comp_modes))
    for mode in block.comp_modes:
        for out in block.outputs:
            scfs[mode][out] = block.get_dynamics(mode,out).coefficient()


    # find a computation mode for fanout that fits the negations of the inputs.
    valid_modes = list(get_valid_modes(scfs,coeffs))
    assert(len(valid_modes) > 0)
    config.set_comp_mode(valid_modes[0])


def connect_stubs_to_sources(board,node_map,mapping):
    groups = arco_util.group_by(mapping, key=lambda args: args[0][0].id)
    for group in groups.values():
        assert(arco_util.all_same(map(lambda n: n[0][0].id, group)))
        node = group[0][0][0]
        outputs = list(map(lambda args: args[0][1],group))
        stubs = list(map(lambda args: args[1],group))
        for output,input_stub in zip(outputs,stubs):
            input_stub.set_source(node,output)

        if isinstance(node,acirc.ABlockInst):
            cs2s_blockinst(board,node,outputs,stubs)

        elif isinstance(node,acirc.AJoin):
            cs2s_join(board,node,outputs,stubs)
        else:
            raise Exception("unknown: %s" % node)
        #print(node.to_str())
        #input()

    print("==========")
    for (node,output),inp in mapping:
        in_varmap = \
            any(map(lambda other_node: other_node.contains(inp), \
                    node_map.values()))
        assert(in_varmap)


# var_map,source_map
def match_stubs_to_sources(sources,stubs):
    var_choices = {}
    var_sources = {}

    # build data structure for choices
    for var,srcmap in sources.items():
        var_choices[var] = []
        for lvl,srcs in srcmap.items():
            var_sources[(var,lvl)] = []
            for src in srcs:
                var_choices[var].append(lvl)
                var_sources[(var,lvl)].append(src)
    # build final choice and stub maps
    choices = []
    all_stubs = []
    for var_name,stubs in stubs.items():
        for stub in stubs:
            selection = []
            for choice in set(var_choices[stub.label]):
                selection.append((stub.label,choice))

            choices.append(selection)
            all_stubs.append(stub)

    # go through each choice
    for choice in itertools.product(*choices):
        outputs = []
        indexes = {}
        invalid = False
        # compute output dictionary
        for var_name,level in choice:
            if not (var_name,level) in indexes:
                indexes[(var_name,level)] = 0

            idx = indexes[(var_name,level)]
            outs_on_level = var_sources[(var_name,level)]
            if idx >= len(outs_on_level):
                invalid = True
                break

            out_block,out_port = outs_on_level[idx]
            outputs.append((out_block,out_port))
            indexes[(var_name,level)] += 1

        if not invalid:
            for (outp,port),stub in zip(outputs,all_stubs):
                print("%s port=%s :> %s" % (outp.name,port,stub))
            yield list(zip(outputs,all_stubs))


def count_var_refs(frag_node_map):
    refs = dict(map(lambda x : (x,0), frag_node_map.keys()))
    stubs = dict(map(lambda x : (x,[]), frag_node_map.keys()))
    # count how many references
    for var_name,frag in frag_node_map.items():
        for stub in filter(lambda n: isinstance(n,acirc.AInput),
                          frag.nodes()):

            if not stub.label in stubs:
                print("=== stub keys ===")
                for key in stubs:
                    print("  %s" % key)
                raise Exception("<%s> of type <%s> not in stubs" % \
                                (stub.label,stub.__class__.__name__))

            stubs[stub.label].append(stub)
            refs[stub.label] += 1

    return refs,stubs
