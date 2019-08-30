if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
from bmark.bmarks.other.bbsys import build_std_bb_sys
import math
import bmark.menvs as menvs

def emit(v):
  return op.Emit(op.Mult(op.Const(0.99999), v), loc="A0")



def model():
    # y'' - u(1-y^2)*y'+y = 0
    # separated
    # y1' = y2
    # y2' = u*(1-y1*y1)*y2 - y1
    prob = MathProg("closed-forced-vanderpol")

    # i reduced mu from 0.2 to 0.05 so that the interval of Y' is between
    # [-2,2]

    rel_time = 5.0
    mu = 0.2
    params = {
      'mu': rel_time*mu,
      'Y0': 0.0,
      'X0': -0.5,
      'tc':1.0*rel_time
    }
    #Y = parse_diffeq('(Y*{mu}*(1.0-{onehack}*X*X) - {onehack}*X)','Y0',':v',params)
    #X = parse_diffeq('{onehack}*Y','X0',':u',params)
    ampl = 1.0
    W,V = build_std_bb_sys(prob,ampl,0)
    params['W'] = W
    Y = parse_diffeq('{tc}*{W}+Y*{mu}*(1.0+(-X)*X)+{tc}*(-X)', \
                     'Y0',':v',params)
    X = parse_diffeq('{tc}*Y','X0',':u',params)

    prob.bind("Y",Y)
    prob.bind("X",X)
    prob.bind("OUTX",op.Emit(op.Var("X"), loc="A0"))
    prob.set_interval("X",-2.0,2.0)
    prob.set_interval("Y",-2.0,2.0)
    prob.set_interval("OUTX",-2.0,2.0)
    prob.set_max_sim_time(20)
    prob.compile()
    menv = menvs.get_math_env('t20')
    return menv,prob

def execute():
  menv,prob = model()
  plot_diffeq(menv,prob)
  plot_phase_portrait(menv,prob,'X','Y')

if __name__ == "__main__":
  execute()
