import itertools
import chip.abs as acirc
import chip.props as prop
import chip.conc_infer as conc_infer
from chip.config import Labels
import ops.aop as aop
import random
import math
import logging
import compiler.arco_pass.route as arco_route
from compiler.arco_pass.rules import get_rules
import compiler.arco_pass.to_abs_op as arcolib_aop
import compiler.arco_pass.to_abs_circ as arcolib_acirc

#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('arco')

# returns number of rules applied, new_ast
def xform_expr(ast,rules,max_xforms=3):
    inputs_space = []

    if ast.op == aop.AOpType.INTEG:
        input_space = list(xform_expr(ast.input(0),rules,
                                      max_xforms=max_xforms))

        input_space.append((0,ast.input(0)))
        inputs_space.append(input_space)
        inputs_space.append([(0,ast.input(1))])

    else:
        for inp in ast.inputs:
            input_space = list(xform_expr(inp,rules,
                                        max_xforms=max_xforms))
            input_space.append((0,inp))
            inputs_space.append(input_space)

    for sel_inputs in itertools.product(*inputs_space):
        n_xforms = sum(map(lambda tup: tup[0], sel_inputs))
        new_inputs = list(map(lambda tup: tup[1], sel_inputs))
        if n_xforms > max_xforms:
            pass

        elif n_xforms == max_xforms:
            yield n_xforms,ast.make(new_inputs)

        else:
            new_ast = ast.make(new_inputs)
            for rule in rules:
                for xformed in rule.apply(new_ast):
                    yield n_xforms + 1,xformed

            yield n_xforms,ast.make(new_inputs)


    if len(inputs_space) == 0:
        for rule in rules:
            for xformed in rule.apply(ast):
                yield 1,xformed




def copy_signal(board,node,output,n_copies,label,max_fanouts):
    sources = []
    if n_copies <= 1:
        #assert(not isinstance(node,acirc.AJoin))
        sources ={0:[(node,output)]}
        yield sources,node,output
        return

    fanout = board.block("fanout")
    for levels in enumerate_tree(fanout,n_copies,
                                 max_blocks=max_fanouts,
                                 permute_input=False):
        free_ports,c_node,c_output = build_tree_from_levels(board,
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


# var_map,source_map
def connect_stubs_to_sources(sources,stubs):
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

def bind_namespace(node,namespace,ids=[]):
    if node.id in ids:
        return

    node.set_namespace(namespace)
    if isinstance(node,acirc.AInput) and \
       not node.source is None:
        new_namespace = node.label
        rslv_node,_ = node.source
        bind_namespace(rslv_node,new_namespace,ids=ids + [node.id])

    else:
        for subn in node.subnodes():
            bind_namespace(subn,namespace,ids=ids + [node.id])

def compile_compute_fragments(board,prob,n_xforms):
    frag_node_map= {}
    frag_output_map= {}
    rules = get_rules()
    for var,expr in prob.bindings():
        abs_expr = arcolib_aop.make_abstract(expr)
        frag_node_map[var] = []
        frag_output_map[var] = []
        for dist_abs_expr in arcolib_aop.distribute_consts(abs_expr):
            for n_xforms,xform_abs_expr in xform_expr(dist_abs_expr,rules):
                for node,output in arcolib_acirc.to_abs_circ(board,xform_abs_expr):
                    if isinstance(node,acirc.ABlockInst):
                        node.config.set_label(output,var,kind=Labels.OUTPUT)

                    if acirc.AbsCirc.feasible(board,[node]):
                        frag_node_map[var].append(node)
                        frag_output_map[var].append(output)

    return frag_node_map,frag_output_map


def compile_sample_fragments_and_add_fanouts(board,frag_node_map, \
                                             frag_output_map):
    while True:
        frag_nodes = {}
        frag_outputs = {}
        print("-> sampling circuit")
        choices = sample(frag_node_map)
        for variable,index in choices.items():
            frag_nodes[variable],_ = \
                                     frag_node_map[variable][index].copy()
            frag_outputs[variable] = frag_output_map[variable][index]

        # compute any references/stubs
        refs,stubs = count_var_refs(frag_nodes)

        subcs = {}
        skip_circuit = False
        # number of free fanouts for variable references
        free_fanouts = board.num_blocks("fanout") - \
                       acirc.AbsCirc.count_instances(board,\
                                    frag_nodes.values())["fanout"]

        for var_name,frag_node in frag_nodes.items():
            frag_output = frag_outputs[var_name]
            subcs[var_name] = []
            # make n copies of each variable for routing purposes.
            for sources,cnode,coutput in \
                copy_signal(board,frag_node,frag_output,
                            refs[var_name], var_name, free_fanouts):

                other_frags = [v for k,v in frag_nodes.items() \
                               if k != var_name]

                if acirc.AbsCirc.feasible(board,[cnode]+other_frags):
                    subcs[var_name].append((sources,cnode,coutput))

            if len(subcs[var_name]) == 0:
                skip_circuit = True
                break

        if skip_circuit:
            print("-> invalid. skipping...")
            continue

        logger.info("--- Fan outs ---")
        for var,frags in subcs.items():
            logger.info("%s: %d" % (var,len(frags)))


        yield subcs

def compile_combine_fragments(subcircuit_optmap):
        variables = []
        subcirc_options = []
        subcirc_sources = {}
        subcirc_nodes = {}
        subcirc_outputs = {}
        for variable,subcirc_opt in subcircuit_optmap.items():
            variables.append(variable)
            subcirc_options.append(range(0,len(subcirc_opt)))
            subcirc_sources[variable] = []
            subcirc_nodes[variable] = []
            subcirc_outputs[variable] = []
            for source,node,output in subcirc_opt:
                subcirc_sources[variable].append(source)
                subcirc_nodes[variable].append(node)
                subcirc_outputs[variable].append(output)


        for select_idx,selection in \
            enumerate(itertools.product(*subcirc_options)):
            source_map = {}
            node_map = {}
            output_map = {}
            for variable,index in zip(variables,selection):
                source_map[variable] = subcirc_sources[variable][index]
                node_map[variable] = subcirc_nodes[variable][index]
                output_map[variable] = subcirc_outputs[variable][index]

            yield select_idx,source_map,node_map,output_map

def compile_apply_mapping(source_map,node_map,output_map,mapping):
    refs,stubs = count_var_refs(node_map)
    for (node,output), input_stub in mapping:
        input_stub.set_source(node,output)

    for (node,output),inp in mapping:
        in_varmap = \
            any(map(lambda other_node: other_node.contains(inp), \
                    node_map.values()))
        assert(in_varmap)


def compile(board,prob,depth=3, \
            max_abs_circs=100, \
            max_fanout_circs=1, \
            max_conc_circs=1):
    frag_node_map,frag_output_map = \
            compile_compute_fragments(board,prob,n_xforms=depth)

    logger.info("--- Fragments ---")
    for var,frags in frag_node_map.items():
        logger.info("====== %s: %d ====" % (var,len(frags)))
        for idx,frag in enumerate(frags):
            print("frag[%d]: %d nodes" % (idx,len(frag.nodes())))
        if len(frags) == 0:
            raise Exception("cannot model variable <%s>" % var)

    num_abs = 0
    for subcircuits_optmap in \
        compile_sample_fragments_and_add_fanouts(board, \
                                                 frag_node_map,
                                                 frag_output_map):

        if num_abs>= max_abs_circs:
            break

        print(">>> combine fragments <<<")
        num_abs += 1
        n_fanout = 0
        for fanout_index,source_map,node_map,output_map in \
            compile_combine_fragments(subcircuits_optmap):

            refs,stubs = count_var_refs(node_map)
            if n_fanout == max_fanout_circs:
                logger.info("-> found %d/%d fanout circuits" % \
                            (n_fanout,max_fanout_circs))
                break

            n_conc = 0;
            print(">>> connect stubs to sources <<<")
            for stub_src_index,mapping in \
                enumerate(connect_stubs_to_sources(source_map,stubs)):

                if n_conc == max_conc_circs:
                    logger.info("-> found %d/%d conc circuits" % \
                                (n_conc,max_conc_circs))
                    break

                print(">>> apply mapping <<<")
                compile_apply_mapping(source_map, \
                                      node_map, \
                                      output_map, \
                                      mapping)

                print(">>> bind namespaces <<<")
                for var,node in node_map.items():
                    bind_namespace(node,var)

                indices = [num_abs,fanout_index,stub_src_index,stub_src_index]
                print(">>> route <<<")
                for route_index,conc_circ in enumerate(arco_route.route(board,
                                                                        prob,
                                                                        node_map)):

                    yield indices+[route_index],conc_circ
                    n_conc += 1
                    n_fanout += 1
                    if n_conc >= max_conc_circs:
                        break


