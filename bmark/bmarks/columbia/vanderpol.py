if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))


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
    prob.set_digital_snr(0.0)
    prob.set_analog_snr(0.0)

    # i reduced mu from 0.2 to 0.05 so that the interval of Y' is between
    # [-2,2]

    params = {
      'mu': 0.2,
      'Y0': 0.0,
      'X0': -0.5,
      'time': 1000,
      'onehack':0.9999
    }
    Y = parse_diffeq('(Y*{mu}*(1.0-{onehack}*X*X) - {onehack}*X)','Y0',':v',params)
    X = parse_diffeq('{onehack}*Y','X0',':u',params)

    prob.bind("Y",Y)
    prob.bind("X",X)
    prob.bind("OUTX",op.Emit(op.Var("X"), loc="A0"))
    prob.set_interval("X",-2.0,2.0)
    prob.set_interval("Y",-2.0,2.0)
    prob.set_interval("OUTX",-2.0,2.0)
    prob.set_max_sim_time(200)
    prob.compile()
    menv = menvs.get_math_env('t200')
    return menv,prob

def execute():
  menv,prob = model()
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute()
