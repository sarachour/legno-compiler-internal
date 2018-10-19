import itertools
import chip.abs as acirc
import compiler.arco_route as arco_route
from compiler.arco_rules import get_rules
import compiler.arco_data as aexpr
import random
import math

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
            yield AGain(const, ast)
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


def enumerate_tree(block,n,max_blocks=None,permute_input=False):
    nels = len(block.inputs) if permute_input \
    else len(block.outputs)

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

def build_tree_from_levels(board,levels,block,input_tree=False):
    blocks = []
    free_ports = {}
    par_ports = block.outputs if input_tree \
                        else block.inputs
    assert(len(par_ports) == 1)
    par_port = par_ports[0]
    child_ports = block.inputs if input_tree \
                  else block.outputs

    for level_idx,n_nodes in enumerate(levels):
        blevel = []
        llports = []
        for idx in range(0,n_nodes):
            node = acirc.ANode.make_node(board,block.name)
            blevel.append(node)
            for port in child_ports:
                llports.append((node,port))

            if idx > 0:
                llnode,llport = llports[0]
                llports = llports[1:]
                if input_tree:
                    acirc.ANode.connect(node,par_port,llnode,llport)
                else:
                    acirc.ANode.connect(llnode,llport,node,par_port)

        blocks.append(blevel)
        for node,port in llports:
            free_ports[level_idx] = llports

    return free_ports,blocks[0][0],par_port


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
                               permute_input=True):

                new_inputs = list(map(lambda inp: \
                                      list(to_abs_circ(board,inp)), \
                                      ast.inputs))

                for _combo in itertools.product(new_inputs):
                    combo = _combo[0]
                    free_ports,out_block,out_port = \
                        build_tree_from_levels(board,
                                               levels,
                                               multiplier,
                                               input_tree=True
                        )

                    for assigns in input_level_combos(free_ports,combo):
                        out_block_c = out_block.copy()
                        for (_dstblk,dstport),(_srcblk,srcport) in assigns:
                            dstblk = _dstblk.copy()
                            srcblk = _srcblk.copy()
                            acirc.ANode.connect(srcblk,srcport, \
                                                dstblk,dstport)

                        print("found: %s" % out_block_c)
                        input()
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
                nnode = node.copy()
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

def sample(xforms):
    frags = {}
    for var_name,choices in xforms.items():
        idx = random.randint(0,len(choices)-1)
        frags[var_name] = choices[idx]

    return frags

def copy_signal(board,node,output,n_copies,label,max_fanouts):
    sources = []
    if n_copies == 1:
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
                                                        input_tree=False
        )
        for level,ports in free_ports.items():
            for port_node,port in ports:
                port_node.config.set_label(port,label)

        new_node = node.copy()
        acirc.ANode.connect(new_node,output,c_node,c_output)
        yield free_ports,c_node,c_output


# var_map,source_map
def route_signals(sources,stubs):
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
            for choice in set(var_choices[stub.name]):
                selection.append((stub.name,choice))

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

    raise NotImplementedError


def count_var_refs(frags):
    refs = dict(map(lambda x : (x,0), frags.keys()))
    stubs = dict(map(lambda x : (x,[]), frags.keys()))
    # count how many references
    for var_name,(frag,_) in frags.items():
        for stub in filter(lambda n: isinstance(n,acirc.AInput),
                          frag.nodes()):

            stubs[stub.name].append(stub)
            refs[stub.name] += 1

    return refs,stubs

def compile(board,prob,depth=3,max_abs_circs=100,max_conc_circs=1):
    permute = {}
    rules = get_rules()
    for var,expr in prob.bindings():
        abs_expr = make_abstract(expr)
        permute[var] = []
        for dist_abs_expr in distribute_consts(abs_expr):
            for n_xforms,xform_abs_expr in xform_expr(dist_abs_expr,rules):
                for node,output in to_abs_circ(board,xform_abs_expr):
                    if acirc.AbsCirc.feasible(board,[node]):
                        permute[var].append((node,output))

    print("--- Fragments ---")
    for var,frags in permute.items():
        print("%s: %d" % (var,len(frags)))
        if len(frags) == 0:
            raise Exception("cannot model one of the variables")

    num_circs = 0
    while num_circs < max_abs_circs:
        frag_map = sample(permute)
        frags = map(lambda args: args[0], frag_map.values())
        refs,stubs = count_var_refs(frag_map)

        if not acirc.AbsCirc.feasible(board,frags):
            print("> not feasible")
            continue


        subcs = {}
        skip_circuit = False

        free_fanouts = board.num_blocks("fanout") - \
                       acirc.AbsCirc.count_instances(board,frags)["fanout"]

        for var_name,(node,output) in frag_map.items():
            subcs[var_name] = []
            for sources,cnode,coutput in \
                copy_signal(board,node,output,
                            refs[var_name], var_name, free_fanouts):

                other_frags = list(map(lambda args: args[1][0],
                                  filter(lambda args: args[0] != var_name,
                                         frag_map.items())))

                if acirc.AbsCirc.feasible(board,[cnode]+other_frags):
                    subcs[var_name].append((sources,cnode,coutput))

            if len(subcs[var_name]) == 0:
                print("> no fanout scheme: %s" % (var_name))
                skip_circuit = True
                break

        if skip_circuit:
            continue

        print("<< circuit <%d> >>" % num_circs)
        print("--- Fan outs ---")
        for var,frags in subcs.items():
            print("%s: %d" % (var,len(frags)))

        variables = subcs.keys()
        choices = list(map(lambda var: subcs[var],variables))

        for choice_idx,choice in \
            enumerate(itertools.product(*choices)):
            var_map = dict(zip(variables,
                               map(lambda args: (args[1],args[2]), choice)))

            source_map = dict(zip(variables,
                                  map(lambda args: args[0],choice)))

            n_conc = 0;
            refs,stubs = count_var_refs(var_map)
            for mapping_idx,mapping in \
                enumerate(route_signals(source_map,stubs)):

                if n_conc == max_conc_circs:
                    print("-> done")
                    break

                for (node,output), input_stub in mapping:
                    input_stub.set_source(node,output)

                for (n,o),inp in mapping:
                    in_varmap = False
                    for e,_ in var_map.values():
                        in_varmap = in_varmap or e.contains(inp)
                    assert(in_varmap)


                idx= [num_circs,choice_idx,mapping_idx]
                basename =  prob.name+ "_".join(map(lambda i:str(i),idx))
                for idx_j,conc_circ in enumerate(arco_route.route(basename,board,var_map)):
                    yield idx+[idx_j],conc_circ
                    n_conc += 1


