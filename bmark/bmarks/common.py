from ops import op, opparse

def parse_fn(expr,params):
    expr_conc = expr.format(**params)
    print(expr_conc)
    return opparse.parse(expr_conc)


def parse_diffeq(expr,ic, handle,params):
    deriv = opparse.parse(expr.format(**params))
    const = params[ic]
    return op.Integ(deriv,op.Const(const),handle=handle)

