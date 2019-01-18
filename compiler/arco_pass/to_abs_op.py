import ops.aop as aop
import itertools

def mab_mult(ast):
  e1 = make_abstract(ast.arg1)
  e2 = make_abstract(ast.arg2)

  constant = ast.coefficient()
  mop_terms = ast.prod_terms()
  aop_terms = list(map(lambda mop: make_abstract(mop), mop_terms))
  if constant == 1.0:
      return aop.AProd(aop_terms)
  else:
      return aop.AGain(constant,
                          aop.AProd(aop_terms))


def mab_sum(ast):
  mop_terms = ast.sum_terms()
  aop_terms = list(map(lambda mop: make_abstract(mop), mop_terms))
  return aop.ASum(aop_terms)

def make_abstract(ast):
    import ops.op as mop
    if ast.op == mop.OpType.VAR:
      return aop.AVar(ast.name)

    elif ast.op == mop.OpType.MULT:
      return mab_mult(ast)

    elif ast.op == mop.OpType.ADD:
      return mab_sum(ast)

    elif ast.op == mop.OpType.CONST:
      return aop.AConst(ast.value)

    elif ast.op == mop.OpType.INTEG:
      deriv = make_abstract(ast.deriv)
      ic = make_abstract(ast.init_cond)
      return aop.AInteg(deriv,ic)

    elif ast.op == mop.OpType.EXTVAR:
      return aop.AExtVar(ast.name)

    elif ast.op == mop.OpType.EMIT:
      expr = make_abstract(ast.args[0])
      return aop.AFunc(aop.AOpType.EMIT, [expr])
    else:
        raise Exception(ast)




def distribute_consts(ast,const=None):
    if ast.op == aop.AOpType.CPROD:
        value = ast.value if const is None else \
                ast.value*const

        for new_expr in distribute_consts(ast.input,const=value):
            yield new_expr

    elif ast.op == aop.AOpType.SUM:
        if not const is None:
            new_input_space = map(lambda inp:
                             list(distribute_consts(inp,const=const)), \
                ast.inputs)

            for new_inputs in itertools.product(*new_input_space):
                yield ast.make(list(new_inputs))

        else:
            yield ast

    elif ast.op == aop.AOpType.VPROD:
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

    elif ast.op == aop.AOpType.CONST:
        if not const is None:
            yield aop.AGain(const, ast)
        else:
            yield ast

    elif ast.op == aop.AOpType.EXTVAR:
        if not const is None:
            yield aop.AGain(const, ast)
        else:
            yield ast


    elif ast.op == aop.AOpType.VAR:
        if not const is None:
            yield aop.AGain(const, ast)
        else:
            yield ast

    elif ast.op == aop.AOpType.INTEG:
        new_deriv_space = list(distribute_consts(ast.input(0),const=const))
        new_ic_space = list(distribute_consts(ast.input(1),const=const))

        for new_deriv,new_ic in itertools \
            .product(*[new_deriv_space,new_ic_space]):
            yield ast.make([new_deriv,new_ic])

    elif ast.op == aop.AOpType.EMIT:
        yield ast

    else:
        raise Exception(ast)

