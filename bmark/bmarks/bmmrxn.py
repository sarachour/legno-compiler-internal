if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../"))

from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import math
import bmark.menvs as menvs


def model():
    prob = MathProg("bmmrxn")
    params = {
        'E0' : 0.44,
        'S0' : 0.64,
        'ES0' : 0.0,
        'kf' : 0.1,
        'kr' : 0.2,
    }
    E = parse_fn('{E0}+0.99999*(-ES)',params)
    S = parse_fn('{S0}+0.99999*(-ES)',params)
    ES = parse_diffeq("{kf}*E*S + {kr}*(-ES)", "ES0", ":z", params)
    prob.bind("E",E)
    prob.bind("S",S)
    prob.bind("ES",ES)
    prob.set_interval("E",0,params['E0'])
    prob.set_interval("S",0,params['S0'])
    max_ES = min(params['E0'],params['S0'])
    prob.set_interval("ES",0,max_ES)
    prob.bind("COMPLEX", op.Emit(op.Var("ES")))
    prob.set_max_sim_time(0)
    prob.compile()
    menv = menvs.get_math_env('t20')
    return menv,prob

def execute():
  menv,prob = model()
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute()
