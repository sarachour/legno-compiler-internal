from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *


def model():
    prob = MathProg("cosc")
    dy2 = op.Add(
        op.Mult(op.Var("dy1"),op.Const(-0.2)),
        op.Mult(op.Var("y"),op.Const(-0.8))
    )
    dy1 = op.Integ(dy2, op.Const(-2),":z")
    y = op.Integ(op.Var("dy1"), op.Const(9),":w")

    params = {
      'V0': -2,
      'P0': 9
    }
    V = parse_diffeq('-0.22*V - 0.84*P', 'P0', ':a', params)
    P = parse_diffeq('V', 'P0', ':b', params)

    prob.bind('V', V)
    prob.bind('P', P)
    prob.bind('Loc', op.Emit(op.Var('P')))
    prob.set_interval("V",-10,10)
    prob.set_interval("P",-10,10)
    prob.set_interval("Loc",-10,10)
    prob.compile()
    return prob
