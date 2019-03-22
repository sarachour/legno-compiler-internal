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
  prob = MathProg("sensor")
  params = {
    'A0': 0,
    'one':0.99999
  }
  prob.bind('P', op.ExtVar('SENSE'))
  prob.bind('X', op.ExtVar('MOTOR'))
  XSQ = parse_fn('X*X',params)
  A = parse_diffeq('{one}*(P-A*XSQ)*XSQ',  \
                           'A0', ':a', params)
  prob.bind('XSQ', XSQ)
  prob.bind('A', A)
  prob.bind('PARAM', op.Emit(op.Var('A')))
  prob.set_interval("A",0,1)
  prob.set_interval("SENSE",0,0.1)
  prob.set_interval("MOTOR",-0.5,0.5)
  prob.set_bandwidth("SENSE",0.002)
  prob.set_bandwidth("MOTOR",0.002)
  prob.set_max_sim_time(2000)
  prob.compile()
  menv = menvs.get_math_env('sensorenv')
  return menv,prob

def execute():
  menv,prob = model()
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute()
