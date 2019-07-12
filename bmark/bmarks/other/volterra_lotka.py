if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))


from bmark.bmarks.common import *
from lang.prog import MathProg
from ops import op, opparse
import bmark.menvs as menvs

def model(tag='simple'):
    prob = MathProg("lotka-%s" % tag)
    params = {
      'a': 0.4,
      'b': 0.3,
      'c': 0.2,
      'd': 0.3,
      "X0": 1.0,
      "Y0": 0.5
    }
    X = parse_diffeq('{a}*X + {b}*(-Z)',"X0",":a",params)
    Y = parse_diffeq('{d}*Z + {c}*(-Y)',"Y0",":b",params)
    Z = parse_fn("X*Y",params)
    prob.bind("Z",Z)
    prob.bind("X",X)
    prob.bind("Y",Y)
    measure_var(prob,"Y", "OUT")
    prob.set_interval("X",0,4)
    prob.set_interval("Y",0,6)
    prob.set_max_sim_time(200)
    prob.compile()
    menv = menvs.get_math_env('t200')
    return menv,prob



def execute():
  menv,prob = model()
  plot_diffeq(menv,prob)


if __name__ == "__main__":
  execute()
