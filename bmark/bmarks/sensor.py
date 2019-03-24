if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import math
import bmark.menvs as menvs

def model(steady=False):
  if steady:
    tag = 'steady'
  else:
    tag = 'diff'
  prob = MathProg("sensor-%s" % tag)
  params = {
    'A0': 0,
    'one':0.99999
  }
  prob.bind('P', op.ExtVar('SENSE'))
  prob.bind('X', op.ExtVar('MOTOR'))
  A = parse_diffeq('{one}*(P*{one}-{one}*A*X)*X',  \
                           'A0', ':a', params)
  prob.bind('A', A)
  prob.bind('PARAM', op.Emit(op.Var('A')))
  prob.set_interval("A",-1.5,1.5)
  prob.set_interval("SENSE",0,0.1)
  prob.set_interval("MOTOR",-0.3,0.3)

  prob.set_bandwidth("SENSE",0.2)
  prob.set_max_sim_time(400)
  if not steady:
    menv = menvs.get_math_env('sendiff')
    prob.set_bandwidth("MOTOR",0.2)
  else:
    menv = menvs.get_math_env('sensteady')
    prob.set_bandwidth("MOTOR",0.2)

  prob.compile()
  return menv,prob

def execute(steady):
  menv,prob = model(steady)
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute(False)
  #execute(True)
