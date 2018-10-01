import blocks as hw
import props
import ops
import units
import itertools
import abs

def compile_V(board,prog):
    raise NotImplementedError

def feasible_bindings(blocks,block,mode,bindings):
    support_analog_signal_conversion = False
    support_digital_to_analog_conversion = False
    block_dict = dict(map(lambda b: (b.name,b), blocks))

    for v,ast in bindings:
        subblock = block_dict[ast.block.block]
        sig = block.signals(v)
        sig2 = subblock.signals(ast.output)

        # detect compatible signals
        if sig != sig2:
            if props.Properties.is_analog(sig) and \
               props.Properties.is_analog(sig2) and \
               support_analog_signal_conversion:
                # FIXME: If we have current to voltage or voltage to current
                # converters, this can be true.
                pass

            elif support_digital_to_analog_conversion:
                # FIXME: If we support hybrid computation, this can be true.
                pass

            else:
                #print("-> mismatched signals")
                return False

        else:
            pass

        prop = block.props(mode,v)
        if prop.type == props.DIGITAL and \
           not ast.expr.op == ast.Op.CONST:
            #print("-> expected constant")
            return False


    return True

def unify(blocks,math_expr,depth=0,use_eq_op=False):
    if depth < 0:
        return

    for block in blocks:
        for output, mode, expr, scale in block.dynamics():
            for is_eq_op, binding_list in expr.match(math_expr):
                block_node = abs.BlockNode(block.name,mode)
                output_node = abs.OutputNode(output,expr)
                output_node.add(block_node)
                all_subcircs = []
                if is_eq_op and not use_eq_op:
                    continue

                bindings = dict(binding_list)
                for v,e in bindings.items():
                    if e.op == ops.Op.VAR or \
                        e.op == ops.Op.CONST:
                        if e.op == ops.Op.CONST and \
                           block.signals(v) == props.DIGITAL:
                            input_node = abs.InputNode(v,e)
                            block_node.add(input_node)

                        elif e.op == ops.Op.CONST \
                             and props.Properties\
                                      .is_analog(block.signals(v)) \
                             and e.value == 0.0:
                            pass

                        else:
                            input_node = abs.InputNode(v,e)
                            block_node.add(input_node)
                            input_node.add(abs.StubNode(e))
                    else:
                        subcircs =list(map(lambda ast: (v,ast),
                                            unify(blocks,e,
                                                    depth=depth-1)))
                        all_subcircs.append(subcircs)

                if depth == 0 and len(all_subcircs) > 0:
                    continue

                for sub_bindings in itertools.product(*all_subcircs):
                    if not feasible_bindings(blocks,block,mode,sub_bindings):
                        continue

                    new_output = output_node.copy()
                    for inp,ast in sub_bindings:
                        inp_node = abs.InputNode(inp,bindings[inp])
                        inp_node.add(ast.copy())
                        new_output.block.add(inp_node)

                    yield new_output


def compile_I_remove_metablocks(circ):
    def remove_fanin():
        node = circ.find(lambda node: node.name == 'block' \
                          and node.block == 'fanin')
        if node is None:
            return False

        fanins = []
        for inp in node.children:
            assert(inp.name == 'input')
            for src in inp.children:
                fanins.append(src)

            inp.remove_children()

        node.remove_children()

        out = node.parent
        upstream_inp = out.parent
        assert(not upstream_inp is None)
        for inp in fanins:
            inp.parent = None
            upstream_inp.add(inp)

        out.parent.remove_child(out)
        node.parent.remove_child(node)
        del out
        del node
        return True

    while remove_fanin():
        continue

    return circ

# TODO: remove identical circuits
def collapse_circuits(circs):
    return circs

def route_consts(board,abs_circ):
    node_map = {}
    const_stub_gen = lambda circ: list(circ.reduce(lambda n: \
                    n if n.name == "stub" \
                    and n.expr.op == ops.Op.CONST else None))

    dacs = list(filter(lambda b : b.type == hw.Block.DAC, board.blocks))
    choices = []
    for stub in const_stub_gen(abs_circ):
        choices.append(list(
            unify(dacs,ops.Const(stub.expr.value),use_eq_op=True,depth=1)
        ))

    for choice in itertools.product(*choices):
        abs_circ_clone = abs_circ.copy()
        for stub,stubast in zip(const_stub_gen(abs_circ_clone),choice):
            stubast.parent = None
            stub.parent.remove_child(stub)
            stub.parent.add(stubast)

        yield abs_circ_clone


def route_vars_to_adcs(board,abs_circ):
    adcs = list(filter(lambda b : b.type == hw.Block.ADC, board.blocks))

    choices = []
    for label in abs_circ.labels:
        choices.append(list(
            unify(adcs,ops.Var(label.name),use_eq_op=True,depth=1)
        ))

    for choice in itertools.product(*choices):
        abs_circ_clone = abs_circ.copy()
        for label,stubast in zip(abs_circ.labels,choice):
            abs_circ_clone.add(abs.ADCLabel(label.name),stubast)

        yield abs_circ_clone


def route_vars_to_fanout(board,abs_circ):
    ref_map = {}
    gen_var_stubs = lambda circ : circ.reduce(lambda n: \
                    n if n.name == "stub" \
                    and n.expr.op == ops.Op.VAR else None)

    # build stubs for routing
    for stub in gen_var_stubs(abs_circ):
        var_name = stub.expr.name
        if not var_name in ref_map:
            ref_map[var_name] = []

        ref_map[var_name].append(stub)


    blocks = list(filter(lambda b : b.type == hw.Block.COPIER, \
                         board.blocks))

    # list of fanout options to use
    all_variables = ref_map.keys()
    fanout_choices = []
    variables = []
    # TODO: support higher branching factors.
    for variable in all_variables:
        num_refs= len(ref_map[variable])
        num_insts = abs_circ.num_instances(variable)
        if num_insts <= num_refs:
            variables.append(variable)
            fanouts = list(unify(blocks,ops.Var(variable),
                                 use_eq_op=True,depth=1)
            )
            fanout_choices.append(fanouts)

    # list of computation asts to use
    gen_choices = []
    for variable in variables:
        generators = list(abs_circ.get_instances(variable))
        gen_choices.append(generators)

    for fanout_choice in itertools.product(*fanout_choices):
        for gen_choice in itertools.product(*gen_choices):
            if len(variables) == 0:
                continue

            fanout_dict = dict(zip(variables,fanout_choice))
            gen_dict = dict(zip(variables,gen_choice))
            new_abs_circ = abs_circ.copy()
            for variable in variables:
                fanout_ast = fanout_dict[variable]
                gen_label,gen_ast = gen_dict[variable]
                fanout_block = board.block(fanout_ast.block.block)
                copies = list(fanout_block.copies(fanout_ast.block.mode,
                                             fanout_ast.output))
                nrefs = new_abs_circ.num_references(variable)
                gen_ast_ref = abs.RefLabel(variable,nrefs)
                new_abs_circ.remove(gen_label)
                new_abs_circ.add(gen_ast_ref,gen_ast)
                for index,copy in enumerate(copies + [fanout_ast.output]):
                    copy_ast = abs.OutputNode(copy,fanout_ast.expr)
                    copy_ast.add(fanout_ast.block.copy())
                    fanout_stubs = gen_var_stubs(copy_ast)
                    assert(len(fanout_stubs) == 1 and \
                       fanout_stubs[0].expr.name == variable)

                    fanout_stub = fanout_stubs[0]
                    fanout_stub.parent.add(abs.ConnNode(gen_ast_ref))
                    fanout_stub.parent.remove_child(fanout_stub)
                    n = new_abs_circ.num_instances(variable)
                    new_abs_circ.add(abs.InstLabel(variable,n),
                                     copy_ast)

            yield new_abs_circ


def route_insts_to_stubs(board,abs_circ):


def route_vars(board,abs_circ):
    def iterative_gen_fanout(circ):
        n = 0
        for new_circ in route_vars_to_fanout(board,circ):
            for result in iterative_gen_fanout(new_circ):
                yield result
            n += 1

        if n == 0:
            yield circ


    for circ in route_vars_to_adcs(board,abs_circ):
        for result in iterative_gen_fanout(circ):
            yield result

def compile_I(board,prog):
    metablocks = []

    current_props = props.AnalogProperties() \
                         .interval(None,None,unit=units.uA)


    fanin = hw.Block('fanin') \
            .add_inputs(props.CURRENT,['in1','in2']) \
            .add_outputs(props.CURRENT,['out']) \
            .set_op("out",ops.Add(ops.Var("in1"),ops.Var("in2"))) \
            .set_prop(["in1","in2","out"],current_props) \
            .check()
    metablocks.append(fanin)


    choices = []
    blocks = list(board.blocks) + metablocks
    for var,expr in prog.bindings():
        subchoices = []
        depth = expr.depth()
        for ast in unify(blocks,expr,depth=depth):
            subchoices.append((var,ast))

        print("%s : %d choices" % (var,len(subchoices)))
        choices.append(collapse_circuits(subchoices))


    for subcircs in itertools.product(*choices):
        abs_circ = abs.AbsCircuit()
        for label,subcirc in subcircs:
            subcirc_nometa = compile_I_remove_metablocks(subcirc)
            abs_circ.add(abs.InstLabel(label),subcirc_nometa)

        for abs_circ1 in route_vars(board,abs_circ):
            for abs_circ2 in route_consts(board,abs_circ1):
                print(abs_circ2)
                input()
                yield abs_circ2


def compile(board, prog):
    if board.mode == hw.Board.CURRENT_MODE:
        for abs_circ in compile_I(board,prog):
            print(abs_circ)

    elif board.mode == hw.Board.VOLTAGE_MODE:
        for abs_circ in compile_V(board,prog):
            print(abs_circ)

    else:
        raise NotImplementedError
