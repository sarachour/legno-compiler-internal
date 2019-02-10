from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs

def model0():
    prob = MathProg("inout0")
    prob.bind('O', op.Emit(op.ExtVar("I")))
    prob.set_bandwidth("I",1e4)
    prob.set_interval("I",-1.0,1.0)
    prob.compile()
    menv = menvs.get_math_env('t2ksin0')
    return menv,prob


def model1():
    prob = MathProg("inout1")
    prob.bind('O', op.Emit(
        op.Mult(op.ExtVar("I"),
                op.Const(0.5))
    ))
    prob.set_bandwidth("I",1e4)
    prob.set_interval("I",0,5)
    prob.set_interval("O",0,5)
    prob.compile()
    menv = menvs.get_math_env('t2ksin1')
    return menv,prob


def model2():
    prob = MathProg("inout2")
    prob.bind('O1', op.Emit(
        op.Mult(op.ExtVar("I1"),
                op.Const(0.5))
    ))
    prob.bind('O2', op.Emit(
        op.Mult(op.ExtVar("I2"),
                op.Const(0.8))
    ))
    prob.set_bandwidth("I1",1e4)
    prob.set_interval("I1",0,5)
    prob.set_bandwidth("I2",1e4)
    prob.set_interval("I2",0,5)
    prob.set_interval("O1",0,5)
    prob.set_interval("O2",0,5)
    prob.compile()
    menv = menvs.get_math_env('t2ksin2')
    return menv,prob
