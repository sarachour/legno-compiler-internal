if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs

def feedback():
  params = {
    'Y0':1.0
  }
  prob = MathProg("feedback")
  Y = parse_diffeq('-Y', 'Y0', ':a', params)
  prob.bind("Y",Y)
  prob.bind("O",op.Emit(op.Var('Y'),loc='A0'))
  prob.set_interval("Y",-1.0,1.0)
  prob.compile()
  menv = menvs.get_math_env('t20')
  prob.set_max_sim_time(20)
  return menv,prob

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

def lut():
    prob = MathProg("testlut")
    # 0.7*[1.0] + 0.25 = 0.95 [the input is 1]
    # 0.7*[0.3] + 0.25 = 0.479
    expr = op.Add(op.Mult(op.Const(0.7),op.Var('T')), op.Const(0.25))
    half_fun = op.Func(['T'], expr)

    prob.bind("A", op.Call([op.Const(0.3)], half_fun))
    prob.bind("OUTPUT", op.Emit(op.Var('A'),loc="A0"))
    prob.set_bandwidth('OUTPUT', 0)
    prob.set_bandwidth('A', 0)
    menv = menvs.get_math_env('t2')
    prob.set_max_sim_time(2)
    prob.compile()
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
