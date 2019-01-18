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
        yield sources,node,output
        return

    fanout = board.block("fanout")
    for levels in arco_util.enumerate_tree(fanout,n_copies,
                                 max_blocks=max_fanouts,
                                 permute_input=False):
        free_ports,c_node,c_output = arco_util.build_tree_from_levels(board,
                                                            levels,
                                                            fanout,
                                                            input_tree=False,
                                                            mode='*',
                                                            prop=prop.CURRENT
        )
        for level,ports in free_ports.items():
            for port_node,port in ports:
                port_node.config.set_label(port,label,kind=Labels.OUTPUT)

        new_node,_ = node.copy()
        acirc.ANode.connect(new_node,output,c_node,c_output)
        yield free_ports,c_node,c_output



def get_valid_modes(mode_map,scf_map):
  for mode,mode_scfs in mode_map.items():
    is_match = True
    for port,scf in scf_map.items():
      if scf != mode_scfs[port]:
        is_match = False

    if is_match:
      yield mode

def connect_stubs_to_sources(board,source_map,node_map,output_map,mapping):
    refs,stubs = count_var_refs(node_map)
    coeff_map = {}
    for (node,output), input_stub in mapping:
        input_stub.set_source(node,output)
        assert(node.block.name == 'fanout')
        assert(isinstance(node,acirc.ABlockInst))
        if not node.id in coeff_map:
          coeff_map[node.id] = {
            'block':node.block,'config':node.config,'coeffs': {}
          }
        coeff_map[node.id]['coeffs'][output] = input_stub.coefficient

    # compute the scaling factors for each mode of the fanout block
    mode_scfs = {}
    block = board.block('fanout')
    for mode in block.comp_modes:
      mode_scfs[mode] = {}
      for out in block.outputs:
        expr = block.get_dynamics(mode,out)
        scf = expr.coefficient()
        mode_scfs[mode][out] = scf

    # find a computation mode for fanout that fits the negations of the inputs.
    for node_id,data in coeff_map.items():
      print(node_id,data['coeffs'])
      valid_modes = list(get_valid_modes(mode_scfs,data['coeffs']))
      assert(len(valid_modes) > 0)
      data['config'].set_comp_mode(valid_modes[0])

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
        for var_name,level in choice:
            if not (var_name,level) in indexes:
                indexes[(var_name,level)] = 0

            idx = indexes[(var_name,level)]
            outs_on_level = var_sources[(var_name,level)]
            if idx >= len(outs_on_level):
                invalid = True
                break

            outputs.append(outs_on_level[idx])
            indexes[(var_name,level)] += 1

        if not invalid:
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
