import itertools
import chip.abs as acirc
import chip.props as prop
import compiler.arco_route as arco_route
from compiler.arco_rules import get_rules
import compiler.arco_data as aexpr
import random
import math
import logging

#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('arco')

# returns number of rules applied, new_ast
def xform_expr(ast,rules,max_xforms=3):
    inputs_space = []

    if ast.op == aexpr.AOp.INTEG:
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


def make_abstract(ast):
    import ops.op as mop
    if ast.op == mop.Op.VAR:
        return aexpr.AVar(ast.name)

    elif ast.op == mop.Op.MULT:
        e1 = make_abstract(ast.arg1)
        e2 = make_abstract(ast.arg2)
        inputs = []
        constant = 1.0

        if e1.op == aexpr.AOp.CPROD:
            constant *= e1.value
            e1 = e1.input

        if e2.op == aexpr.AOp.CPROD:
            constant *= e2.value
            e2 = e2.input

        if e1.op == aexpr.AOp.VPROD:
            inputs += e1.inputs

        else:
            inputs += [e1]

        if e2.op == aexpr.AOp.VPROD:
            inputs += e2.inputs
        else:
            inputs += [e2]

        red_inputs = list(filter(lambda x: not x.op == aexpr.AOp.CONST, inputs))
        if constant == 1.0:
            return aexpr.AProd(red_inputs)
        else:
            return aexpr.AGain(constant,
                               aexpr.AProd(red_inputs))

    elif ast.op == mop.Op.ADD:
        e1 = make_abstract(ast.arg1)
        e2 = make_abstract(ast.arg2)
        inputs = []
        if e1.op == aexpr.AOp.SUM:
            inputs += e1.inputs
        else:
            inputs += [e1]

        if e2.op == aexpr.AOp.SUM:
            inputs += e2.inputs
        else:
            inputs += [e2]

        return aexpr.ASum(inputs)

    elif ast.op == mop.Op.CONST:
        return aexpr.AGain(ast.value,aexpr.AConst())

    elif ast.op == mop.Op.INTEG:
        deriv = make_abstract(ast.deriv)
        ic = make_abstract(ast.init_cond)
        return aexpr.AInteg(deriv,ic)

    elif ast.op == mop.Op.EMIT:
        expr = make_abstract(ast.args[0])
        return aexpr.AFunc(aexpr.AOp.EMIT, [expr])
    else:
        raise Exception(ast)

def distribute_consts(ast,const=None):
    if ast.op == aexpr.AOp.CPROD:
        value = ast.value if const is None else \
                ast.value*const

        for new_expr in distribute_consts(ast.input,const=value):
            yield new_expr

    elif ast.op == aexpr.AOp.SUM:
        if not const is None:
            new_input_space = map(lambda inp:
                             list(distribute_consts(inp,const=const)), \
                ast.inputs)

            for new_inputs in itertools.product(*new_input_space):
                yield ast.make(list(new_inputs))

        else:
            yield ast

    elif ast.op == aexpr.AOp.VPROD:
        if not const is None:
            new_input_space = list(map(lambda inp:
                                list(distribute_consts(inp,const=const)),
                                ast.inputs))

            for new_inputs in itertools.product(*new_input_space):
                for idx,new_inp in enumerate(new_inputs):
                    inputs = list(ast.inputs)
                    inputs[idx] = new_inp
                    yield ast.make(inputs)

        else:
            yield ast

    elif ast.op == aexpr.AOp.CONST:
        if not const is None:
            yield aexpr.AGain(const, ast)
        else:
            yield ast

    elif ast.op == aexpr.AOp.VAR:
        if not const is None:
            yield aexpr.AGain(const, ast)
        else:
            yield ast

    elif ast.op == aexpr.AOp.INTEG:
        new_deriv_space = list(distribute_consts(ast.input(0),const=const))
        new_ic_space = list(distribute_consts(ast.input(1),const=const))

        for new_deriv,new_ic in itertools \
            .product(*[new_deriv_space,new_ic_space]):
            yield ast.make([new_deriv,new_ic])

    elif ast.op == aexpr.AOp.EMIT:
        yield ast

    else:
        raise Exception(ast)


def enumerate_tree(block,n,max_blocks=None,mode='default',
                   permute_input=False,prop=prop.CURRENT):
    nels = len(block.by_property(prop,mode,block.inputs)) if permute_input \
       else len(block.by_property(prop,mode,block.outputs))

    def count_free(levels):
        cnt = 0
        for idx in range(0,len(levels)):
            if idx == len(levels)-1:
                cnt += levels[idx]*nels

            else:
                cnt += levels[idx]*nels-levels[idx+1]

        return cnt

    levels = [1]
    max_depth = int(math.ceil(n/(nels-1)))
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
                           mode='default',
                           prop=None):
    blocks = []
    free_ports = {}

    par_ports = block.by_property(prop,mode,block.outputs) if input_tree \
       else block.by_property(prop,mode,block.inputs)

    assert(len(par_ports) == 1)
    par_port = par_ports[0]

    child_ports = block.by_property(prop,mode,block.inputs) if input_tree \
                  else block.by_property(prop,mode,block.outputs)

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


def to_abs_circ(board,ast):
    if ast.op == aexpr.AOp.INTEG:
        for deriv,deriv_output in to_abs_circ(board,ast.input(0)):
            ic = ast.input(1)
            if not (ic.op == aexpr.AOp.CPROD and ic.input.op == aexpr.AOp.CONST):
                raise Exception("unexpected ic: <%s>" % ic)
            init_cond = ic.value

            node = acirc.ANode.make_node(board,"integrator")
            node.config.set_dac("ic",init_cond)

            acirc.ANode.connect(deriv,deriv_output,node,"in")
            yield node,"out"

    elif ast.op == aexpr.AOp.VPROD:
        if len(ast.inputs) == 1:
            for node,output in to_abs_circ(board,ast.input(0)):
                yield node,output

        else:
            multiplier = board.block("multiplier")
            for levels in \
                enumerate_tree(multiplier,len(ast.inputs),
                               mode='default',
                               permute_input=True,
                               prop=prop.CURRENT):

                new_inputs = list(map(lambda inp: \
                                      list(to_abs_circ(board,inp)), \
                                      ast.inputs))

                for combo in itertools.product(*new_inputs):
                    free_ports,out_block,out_port = \
                        build_tree_from_levels(board,
                                               levels,
                                               multiplier,
                                               input_tree=True,
                                               mode='default',
                                               prop=prop.CURRENT
                        )

                    for assigns in input_level_combos(free_ports,combo):
                        out_block_c,copier = out_block.copy()
                        for (_dstblk,dstport),(_srcblk,srcport) in assigns:
                            dstblk = copier.get(_dstblk)
                            srcblk,_ = _srcblk.copy()
                            acirc.ANode.connect(srcblk,srcport, \
                                                dstblk,dstport)
                        yield out_block_c,out_port


    elif ast.op == aexpr.AOp.CPROD and ast.input.op == aexpr.AOp.CONST:
        node = acirc.ANode.make_node(board,"tile_dac")
        node.config.set_dac("in",ast.value)
        yield node,"out"

    elif ast.op == aexpr.AOp.CPROD:
        for qnode,qnode_output in to_abs_circ(board,ast.input):
            node = acirc.ANode.make_node(board,"multiplier")
            node.config.set_mode("vga").set_dac("coeff",ast.value)
            acirc.ANode.connect(qnode,qnode_output,node,"in0")
            yield node,"out"

    elif ast.op == aexpr.AOp.CONST:
        node = circ.make_node("tile_dac")
        node.config.set_dac("in",1.0)
        yield node,"out"

    elif ast.op == aexpr.AOp.VAR:
        stub = acirc.AInput(ast.name)
        yield stub,"out"

    elif ast.op == aexpr.AOp.SUM:
        new_inputs = list(map(lambda inp: list(to_abs_circ(board,inp)), \
                                 ast.inputs))

        for combo in itertools.product(*new_inputs):
            join = acirc.AJoin()
            for node,out in combo:
                nnode,_ = node.copy()
                assert(not nnode is None)
                acirc.ANode.connect(nnode,out,join,"in")

            yield join,"out"

    elif ast.op == aexpr.AOp.EMIT:
        for in_node,in_port in to_abs_circ(board,ast.input(0)):
            node = acirc.ANode.make_node(board,"due_adc")
            acirc.ANode.connect(in_node,in_port,node,"in")
            yield node,"out"

    else:
        raise Exception("unsupported: %s" % ast)

def sample(optmap):
    choice = {}
    for var_name,choices in optmap.items():
        idx = random.randint(0,len(choices)-1)
        choice[var_name] = idx

    return choice

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
                                                            mode='default',
                                                            prop=prop.CURRENT
        )
        for level,ports in free_ports.items():
            for port_node,port in ports:
                port_node.config.set_label(port,label)

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


def compile_compute_fragments(board,prob,n_xforms):
    frag_node_map= {}
    frag_output_map= {}
    rules = get_rules()
    for var,expr in prob.bindings():
        abs_expr = make_abstract(expr)
        frag_node_map[var] = []
        frag_output_map[var] = []
        for dist_abs_expr in distribute_consts(abs_expr):
            for n_xforms,xform_abs_expr in xform_expr(dist_abs_expr,rules):
                for node,output in to_abs_circ(board,xform_abs_expr):
                    if acirc.AbsCirc.feasible(board,[node]):
                        frag_node_map[var].append(node)
                        frag_output_map[var].append(output)

    return frag_node_map,frag_output_map


def compile_sample_fragments_and_add_fanouts(board,frag_node_map, \
                                             frag_output_map):
    while True:
        frag_nodes = {}
        frag_outputs = {}
        choices = sample(frag_node_map)
        for variable,index in choices.items():
            frag_nodes[variable] = frag_node_map[variable][index]
            frag_outputs[variable] = frag_output_map[variable][index]
        # compute any references/stubs
        refs,stubs = count_var_refs(frag_nodes)

        subcs = {}
        skip_circuit = False
        # number of free fanouts for variable references
        free_fanouts = board.num_blocks("fanout") - \
                       acirc.AbsCirc.count_instances(board,frag_nodes.values())["fanout"]

        for var_name,frag_node in frag_nodes.items():
            frag_output = frag_outputs[var_name]
            subcs[var_name] = []
            # make n copies of each variable for routing purposes.
            for sources,cnode,coutput in \
                copy_signal(board,frag_node,frag_output,
                            refs[var_name], var_name, free_fanouts):

                other_frags = [v for k,v in frag_nodes.items() if k != var_name]
                if acirc.AbsCirc.feasible(board,[cnode]+other_frags):
                    subcs[var_name].append((sources,cnode,coutput))

            if len(subcs[var_name]) == 0:
                logger.warn("> no fanout scheme: %s" % (var_name))
                skip_circuit = True
                break

        if skip_circuit:
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
            any(map(lambda other_node: other_node.contains(inp), node_map.values()))
        assert(in_varmap)


def compile(board,prob,depth=3,max_abs_circs=100,max_conc_circs=1):
    frag_node_map,frag_output_map = \
            compile_compute_fragments(board,prob,n_xforms=depth)

    logger.info("--- Fragments ---")
    for var,frags in frag_node_map.items():
        logger.info("====== %s: %d ====" % (var,len(frags)))
        if len(frags) == 0:
            raise Exception("cannot model variable <%s>" % var)

    num_abs = 0
    for subcircuits_optmap in \
        compile_sample_fragments_and_add_fanouts(board, \
                                                 frag_node_map,
                                                 frag_output_map):

        if num_abs>= max_abs_circs:
            break

        for fanout_index,source_map,node_map,output_map in \
            compile_combine_fragments(subcircuits_optmap):

            refs,stubs = count_var_refs(node_map)

            n_conc = 0;
            for stub_src_index,mapping in \
                enumerate(connect_stubs_to_sources(source_map,stubs)):

                if n_conc == max_conc_circs:
                    logger.info("-> done")
                    break

                compile_apply_mapping(source_map,node_map,output_map,mapping)

                indices = [num_abs,fanout_index,stub_src_index,stub_src_index]
                basename =  prob.name+ "_".join(map(lambda i:str(i),indices))
                for route_index,conc_circ in enumerate(arco_route.route(basename,
                                                                        board,
                                                                        node_map)):

                    yield indices+[route_index],conc_circ
                    n_conc += 1

                    if n_conc >= max_conc_circs:
                        break


        num_abs += 1
