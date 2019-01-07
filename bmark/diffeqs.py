from lang.prog import MathProg
from ops import op
'''
def benchmark_smmrxn():
    prob = MathProg("smmrxn")
    kf = 0.5
    kr = 0.1
    E0 = 1.2
    S0 = 2.4
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
    prob.interval("E",0,E0)
    prob.interval("S",0,S0)
    prob.interval("ES",0,min(E0,S0))
    prob.interval("enz-sub",0,min(E0,S0))
    prob.bind("enz-sub", op.Emit(op.Var("ES")))
    prob.compile()
    return prob


def benchmark_bmmrxn():
    prob = MathProg("bmmrxn")
    kf = 0.1
    kr = 0.05
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
    prob.interval("E",0,E0)
    prob.interval("S",0,S0)
    prob.interval("ES",0,min(E0,S0))
    prob.interval("enz-sub",0,min(E0,S0))
    prob.bind("enz-sub", op.Emit(op.Var("ES")))
    prob.compile()
    return prob
'''

def benchmark_p53stoch():
    raise Exception("not implemented")


def benchmark_reprissilator():
    raise Exception("not implemented")


def benchmark_spring():
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
    prob.interval("Y",-10,10)
    prob.interval("y",-10,10)
    prob.interval("dy1",-10,10)
    # compute fmin and fmax for each signal.
    prob.compile()
    return prob

'''
def benchmark_decay():
    prob = MathProg("decay")
    x = op.Integ(
        op.Mult(op.Var("x"),op.Const(-0.05)), \
        op.Const(5), \
        ':x')
    prob.bind("x",x)
    prob.bind("X", op.Emit(op.Var("x")))
    prob.interval("x",0,5)
    prob.interval("X",0,5)

    prob.compile()
    return prob
'''

def benchmark_vanderpol():
    # y'' - u(1-y^2)*y'+y = 0
    # separated
    # y1' = y2
    # y2' = u*(1-y1*y1)*y2 - y1
    prob = MathProg("vanderpol")
    mu = 1000
    y1_ic = 2
    y2_ic = 0
    dy1 = op.Var("y2")
    dy2 = op.Add(
        op.Mult(
            op.Mult(
                op.Const(-mu),
                op.Var("y2")
            ),
            op.Add(
                op.Const(-1),
                op.Mult(op.Var('y1'),
                        op.Var('y1'))
            )
        ),
        op.Mult(
            op.Const(-1),
            op.Var('y1')
        )
    )

    prob.bind("y1",
              op.Integ(dy1, op.Const(y1_ic),
                       ":u"))
    prob.bind("y2",
              op.Integ(dy2, op.Const(y2_ic),
                       ":v"))
    prob.interval("y1",0,5)
    prob.interval("y2",0,5)
    prob.bind("Y", op.Emit(op.Var("y1")))

def benchmark_inout1():
    prob = MathProg("inout1")
    prob.bind('O', op.Emit(
        op.Mult(op.ExtVar("I"),
                op.Const(0.5))
    ))
    prob.bandwidth("I",1e4)
    prob.interval("I",0,5)
    prob.interval("O",0,5)
    prob.compile()
    return prob


def benchmark_inout2():
    prob = MathProg("inout2")
    prob.bind('O1', op.Emit(
        op.Mult(op.ExtVar("I1"),
                op.Const(0.5))
    ))
    prob.bind('O2', op.Emit(
        op.Mult(op.ExtVar("I2"),
                op.Const(0.8))
    ))
    prob.bandwidth("I1",1e4)
    prob.interval("I1",0,5)
    prob.bandwidth("I2",1e4)
    prob.interval("I2",0,5)
    prob.interval("O1",0,5)
    prob.interval("O2",0,5)
    prob.compile()
    return prob

BMARKS = [
    benchmark_spring(),
    benchmark_inout1(),
    benchmark_inout2(),
    benchmark_vanderpol()
]

def get_prog(name):
    for bmark in BMARKS:
        if bmark.name == name:
            return bmark

    raise Exception("unknown benchmark: <%s>" % name)
