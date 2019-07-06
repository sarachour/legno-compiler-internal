if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))


from bmark.bmarks.common import *
from lang.prog import MathProg
from ops import op, opparse
import bmark.menvs as menvs

def model():
    prob = MathProg("lotka")
    params = {
      'a': 0.5,
      'b': 0.99999,
      'd': 0.99999,
      'g': 0.99999,
      "X0": 0.9999,
      "Y0": 0.99999
    }
    X = parse_diffeq('{a}*X + {b}*(-Z)',"X0",":a",params)
    Y = parse_diffeq('{g}*Z + {d}*(-Y)',"Y0",":b",params)
    Z = parse_fn("X*Y",params)
    prob.bind("Z",Z)
    prob.bind("X",X)
    prob.bind("Y",Y)
    prob.bind("OUT",op.Emit(op.Var("Y"), \
                            loc="A0"))

    #prob.bind("OUT",op.Emit(op.Mult(op.Const(0.9999),
    #                                op.Var("Y")), \
    #                        loc="A0"))
    prob.set_interval("X",-1.7,1.7)
    prob.set_interval("Y",1.0,1.0)
    prob.set_max_sim_time(20)
    prob.compile()
    menv = menvs.get_math_env('t20')
    return menv,prob



def execute():
  menv,prob = model()
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute()
