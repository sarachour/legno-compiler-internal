
def add_test(experiment=None):
    prob = MathProg("test-")

def benchmark_smmrxn(experiment=None):
    prob = MathProg("test2")
    kf = 1e-4
    kr = 1e-2
    E0 = 4400
    S0 = 6600
    ES = op.Integ(op.Add(
        op.Mult(op.Const(kf),
                op.Mult(op.Var("S"),op.Var("E"))),
        op.Mult(op.Const(-1*kr),op.Var("ES"))), op.Const(0),
                  handle=':z')

    E = op.Add(op.Const(E0),
               op.Mult(op.Var("ES"), op.Const(-1)))

    S = op.Add(op.Const(S0),
               op.Mult(op.Var("ES"), op.Const(-1)))

    prob.bind("E",E)
    prob.bind("S",S)
    prob.bind("ES",ES)
    prob.interval("E",0,4400)
    prob.interval("S",0,6800)
    prob.interval("ES",0,4400)
    prob.interval("enz-sub",0,4400)
    prob.bind("enz-sub", op.Emit(op.Var("ES")))
    prob.compile()
    return prob

from lang.prog import MathProg
from ops import op

def benchmark_spring(experiment=None):
    prob = MathProg("spring")
    dy2 = op.Add(
        op.Mult(op.Var("dy1"),op.Const(-0.2)),
        op.Mult(op.Var("y"),op.Const(-0.8))
    )
    dy1 = op.Integ(dy2, op.Const(-2),":z")
    y = op.Integ(op.Var("dy1"), op.Const(9),":w")

    prob.bind("dy1",dy1)
    prob.bind("y",y)
    prob.bind("Y", op.Emit(op.Var("y")))
    prob.interval("Y",-1,1)
    prob.interval("y",-1,1)
    prob.interval("dy1",-2,2)
    # compute fmin and fmax for each signal.
    prob.compile()
    return prob


def benchmark_decay(experiment=None):
    prob = MathProg("decay")
    x = op.Integ(
        op.Mult(op.Var("x"),op.Const(-0.5)), \
        op.Const(5), \
        'x')
    prob.bind("x",x)
    prob.bind("X", op.Emit(op.Var("x")))
    prob.interval("x",0,5)
    prob.interval("X",0,5)

    prob.compile()
    return prob

_BMARKS = {
    'decay' : benchmark_decay,
    'spring' : benchmark_spring,
    'smmrxn' : benchmark_smmrxn,
}

def get_bmark(name,experiment=None):
    if name in _BMARKS:
        return _BMARKS[name](experiment)
    else:
        raise Exception("unknown benchmark")
