if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
from bmark.bmarks.other.bbsys import build_bb_sys
import math
import bmark.menvs as menvs

def emit(v):
  return op.Emit(op.Mult(op.Const(0.99999), v))
 
def model():
  prob = MathProg("sensor-fanout")
  prob.set_digital_snr(10.0)
  ampl,freq = 0.5,0.99
  SENSE,_ = build_bb_sys(prob,ampl,freq,0)
  #ampl,freq = 0.5,0.99
  #MOTOR,_ = build_bb_sys(prob,ampl,freq,1)
  params = {
    'A0': 0,
    'one':0.99999,
    'sense':SENSE,
    'motor':SENSE
  }
  A = parse_diffeq('{one}*(({one}*{sense})+A*({one}*(-{motor})))*{motor}',  \
                           'A0', ':q', params)
  prob.bind('A', A)
  prob.bind('PARAM', emit(op.Var('A')))
  #prob.bind('MOTOR', emit(op.Var(SENSE)))

  prob.set_interval("A",-1.5,1.5)

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
