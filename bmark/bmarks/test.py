if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs

def nochange():
    prob = MathProg("nochange")
    params = {'Y0': 0.0}
    Y = parse_diffeq('0.1', 'Y0', ':a', params)
    prob.bind('Y', Y)
    prob.bind("O",op.Emit(op.Var('Y'),loc='A0'))
    prob.set_interval("Y",-1.0,1.0)
    prob.compile()
    menv = menvs.get_math_env('t2')
    prob.set_max_sim_time(2)
    return menv,prob

def model_1():
    prob = MathProg("mod1")
    prob.bind('X', op.ExtVar("I"))
    prob.bind('O', op.Emit(op.Var("X")))
    prob.set_bandwidth("I",1e-2)
    prob.set_interval("I",-1.0,1.0)
    prob.set_max_sim_time(2000)
    prob.compile()
    menv = menvs.get_math_env('t2ksin0')
    return menv,prob


def model_1_scale():
    prob = MathProg("mod1scale")
    prob.bind('X', op.ExtVar("I"))
    prob.bind('O', op.Emit(
        op.Mult(op.Var("X"),
                op.Const(0.5))
    ))
    prob.set_bandwidth("I",1e-2)
    prob.set_interval("I",-5.0,5.0)
    prob.set_max_sim_time(2000)
    prob.compile()
    menv = menvs.get_math_env('t2ksin1')
    return menv,prob


def model_2():
    prob = MathProg("mod2")
    prob.bind('X1', op.ExtVar("I1"))
    prob.bind('X2', op.ExtVar("I2"))
    prob.bind('O', op.Emit(
        op.Mult(op.Var("X2"),
                op.Const(0.8))
    ))
    prob.set_bandwidth("I1",1e-2)
    prob.set_bandwidth("I2",1)
    prob.set_interval("I1",-1,1)
    prob.set_interval("I2",-1,1)
    prob.set_max_sim_time(200)
    prob.compile()
    menv = menvs.get_math_env('t2ksin2')
    return menv,prob

def model_2_add():
    prob = MathProg("mod2add")
    prob.bind('X1', op.ExtVar("I1"))
    prob.bind('X2', op.ExtVar("I2"))
    prob.bind('O', op.Emit(
          op.Add(
            op.Var("X1"),
            op.Var("X2"))
        )
    )
    prob.set_bandwidth("I1",1e-2)
    prob.set_bandwidth("I2",1)
    prob.set_interval("I1",-1,1)
    prob.set_interval("I2",-1,1)
    prob.set_max_sim_time(200)
    prob.compile()
    menv = menvs.get_math_env('t2ksin2')
    return menv,prob


def model_1_sqrt():
    prob = MathProg("mod1sqrt")
    spec_fun = op.Func(['V'], op.Mult(op.Sgn(op.Var('V')),\
                                      op.Sqrt(op.Abs(op.Var('V')))))
    prob.bind('X', op.ExtVar("I"))
    prob.bind('O', op.Emit(op.Call([op.Var("X")], spec_fun)))
    prob.set_bandwidth("I",1e-2)
    prob.set_interval("I",-1.0,1.0)
    prob.set_max_sim_time(2000)
    prob.compile()
    menv = menvs.get_math_env('t2ksin0')
    return menv,prob

def model_1_sin():
    prob = MathProg("mod1sin")
    spec_fun = op.Func(['V'], op.Mult(op.Const(-1.0),
                                      op.Sin(op.Var('V'))))
    prob.bind('X', op.ExtVar("I"))
    prob.bind('O', op.Emit(op.Call([op.Var("X")], spec_fun)))
    prob.set_bandwidth("I",1e-2)
    prob.set_interval("I",-1.0,1.0)
    prob.set_max_sim_time(2000)
    prob.compile()
    menv = menvs.get_math_env('t2ksin0')
    return menv,prob



def execute(menv,prob):
  T,Y = run_fxn(menv,prob)
  plot_fxn(menv,prob,T,Y)


if __name__ == "__main__":
  for model in [model_1, model_1_scale,
                model_2,model_2_add,
                model_1_sqrt,
                model_1_sin]:
    menv,prob = model()
    print(prob.name)
    execute(menv,prob)
