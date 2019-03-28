if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
from bmark.bmarks.bbsys import build_bb_sys
import math
import bmark.menvs as menvs

def emit(v):
  return op.Emit(op.Mult(op.Const(0.99999), v))


def model():
  prob = MathProg("sensor-dynsys")
  ampl,freq = 0.5,0.99
  SENSE,_ = build_bb_sys(prob,ampl,freq,0)
  MOTOR = "M"
  prob.bind(MOTOR, op.Mult(op.Var(SENSE), op.Var(SENSE)))

  params = {
    'A0': 0,
    'one':0.99999,
    'sense':SENSE,
    'motor':MOTOR,
    'reltau':10.0
  }
  A = parse_diffeq('(({reltau}*{sense})+{reltau}*(A*(-{motor})))*{motor}',  \
                           'A0', ':q', params)
  prob.bind('A', A)
  prob.set_interval("A",-1.5,1.5)

  prob.bind('PARAM', emit(op.Var('A')))
  #prob.bind('MOTOR', emit(op.Var(MOTOR)))
  prob.set_max_sim_time(200)
  menv = menvs.get_math_env('t200')

  prob.compile()
  return menv,prob

def execute():
  menv,prob = model()
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute()
