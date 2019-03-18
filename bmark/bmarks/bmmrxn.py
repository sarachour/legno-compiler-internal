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
      'E0' : 0.9999,
      'S0' : 0.9999,
      'ES0' : 0.0,
      'kf' : 0.01,
      'kr' : 0.09999,
      'one': 0.9999,
    }
    E = parse_fn('{E0}+{one}*(-ES)',params)
    S = parse_fn('{S0}+{one}*(-ES)',params)
    ES = parse_diffeq("({one}*({kf}*E)*S) + {kr}*(-ES)", "ES0", ":z", params)
    prob.bind("E",E)
    prob.bind("S",S)
    prob.bind("ES",ES)
    prob.set_interval("E",0,params['E0'])
    prob.set_interval("S",0,params['S0'])
    max_ES = min(params['E0'],params['S0'])
    prob.set_interval("ES",-max_ES,max_ES)
    prob.bind("COMPLEX", op.Emit(op.Var("ES")))
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
