if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../"))


from bmark.bmarks.common import *
from lang.prog import MathProg
from ops import op, opparse
import bmark.menvs as menvs

def model():
    # y'' - u(1-y^2)*y'+y = 0
    # separated
    # y1' = y2
    # y2' = u*(1-y1*y1)*y2 - y1
    prob = MathProg("vanderpol")
    params = {
        'mu': 0.2,
        'Y0': 0.0,
        'X0': -0.5,
        'time': 100
    }
    Y = parse_diffeq('(Y*{mu}*(1.0-X*X) - X)','Y0',':v',params)
    X = parse_diffeq('Y','X0',':u',params)

    prob.bind("X",X)
    prob.bind("Y",Y)
    prob.bind("y",op.Emit(op.Var("Y")))
    prob.set_interval("X",-2.2,2.2)
    prob.set_interval("Y",-2.2,2.2)
    prob.set_interval("y",-2.2,2.2)
    prob.compile()
    menv = menvs.get_math_env('t200')
    return menv,prob

def execute():
  menv,prob = model()
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute()
