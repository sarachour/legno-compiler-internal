if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../"))


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

def model3():
    prob = MathProg("inout3")
    spec_fun = op.Func(['V'], op.Mult(op.Sgn(op.Var('V')),\
                                      op.Sqrt(op.Abs(op.Var('V')))))
    prob.bind('O', op.Emit(op.Call([op.ExtVar("I")], spec_fun)))
    prob.set_bandwidth("I",1e4)
    prob.set_interval("I",-1.0,1.0)
    prob.compile()
    menv = menvs.get_math_env('t2ksin0')
    return menv,prob


def execute(menv,prob):
  T,Y = run_fxn(menv,prob)
  plot_fxn(menv,prob,T,Y)


if __name__ == "__main__":
  menv,prob = model0()
  execute(menv,prob)
  menv,prob = model1()
  execute(menv,prob)
  menv,prob = model2()
  execute(menv,prob)
  menv,prob = model3()
  execute(menv,prob)
