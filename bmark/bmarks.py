
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
        op.Mult(op.Const(-1*kr),op.Var("ES"))), op.Const(0))

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
    #prob.bind("_y", op.Emit(op.Var("y")))
    prob.compile()
    return prob

def benchmark2(experiment=None):
    prob = MathProg("test")

    term0 = op.Const(1.5*0.5)
    term1 = op.Mult(op.Const(0.6*0.5),op.Var("x1"))
    term2 = op.Mult(op.Var("x0"),op.Var("x0"))
    term3 = op.Var("x0")

    # compilation is performing transformations than compiling.
    x2 = op.Mult(op.Const(0.5),
                        op.Add(term0,
                                op.Mult(op.Const(-1.0),
                                        op.Add(term1,op.Add(term2,term3)))))

    prob.bind("x1",op.Integ(x2, op.Const(0)))
    prob.bind("x0",op.Integ(op.Var("x1"), op.Const(-1)))

    prob.interval("x1",-100,100)
    prob.interval("x0",-100,100)

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
    dy1 = op.Integ(dy2, op.Const(-2),"dy1")
    y = op.Integ(op.Var("dy1"), op.Const(9),"y")

    prob.bind("dy1",dy1)
    prob.bind("y",y)
    prob.interval("y",-1,1)
    prob.interval("dy1",-2,2)
    # compute fmin and fmax for each signal.
    prob.compile()
    prob.bind("Y", op.Emit(op.Var("y")))
    return prob


def benchmark0(experiment=None):
    prob = MathProg("bmark0")
    prob.read("x")
    prob.emit("y")
    prob.bind("y", op.Mult(op.Var("x"), op.Const(2.0)))
    return prob

_BMARKS = {
    'bmark0' : benchmark0,
    'spring' : benchmark_spring,
    'bmark2' : benchmark2,
    'smmrxn' : benchmark_smmrxn,
}

def get_bmark(name,experiment=None):
    if name in _BMARKS:
        return _BMARKS[name](experiment)
    else:
        raise Exception("unknown benchmark")
