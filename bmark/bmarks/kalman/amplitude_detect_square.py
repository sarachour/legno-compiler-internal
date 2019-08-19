if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))

from bmark.bmarks.common import *
from lang.prog import MathProg
from ops import op, opparse
import bmark.menvs as menvs
from bmark.bmarks.other.closed_form import *


def model():
  params = {
    'meas_noise':0.0,
    'proc_noise':0.02,
    'X0':1.0,
    'P0':1.0,
    'Q0':0.0,
    'one':0.9999
  }
  prob = MathProg("KAmplDetectSq")

  '''
  K tracks a constant signal that is constantly
  flipping from 1 to -1. There is no carrier signal
  (it's just a dc offset)
  '''
  #params['Q'] = params['meas_noise']
  params['Rinv'] = 1.0/params['proc_noise']
  params['nRinv'] = -1.0/params['proc_noise']

  build_cos(prob,"0.3",0.3,"DFREQ")
  data_fn = op.Func(['V'], op.Add(
    op.Const(0.5),
    op.Mult(op.Sgn(op.Var('V')), op.Const(0.3)) \
  ))

  Z = op.Call([op.Var("DFREQ")], data_fn)
 
  dX = parse_diffeq("{Rinv}*P*E", \
                    "X0", \
                    ":x", \
                    params)
  E = parse_fn("{one}*Z+{one}*(-X)",params)

  dP = parse_diffeq("0.5+{nRinv}*P*P", \
                    "P0", \
                    ":p", \
                    params)


  measure_var(prob,"X","SIG")
  prob.bind("E",E)
  prob.bind("P",dP)
  prob.bind("Z",Z)
  prob.bind("X",dX)
  prob.set_interval("X",-1.0,1.0)
  prob.set_interval("P",-1.0,1.0)
  prob.set_max_sim_time(50)
  prob.compile()
  menv = menvs.get_math_env('t50')
  return menv,prob



def execute():
  menv,prob = model()
  plot_diffeq(menv,prob)


if __name__ == "__main__":
  execute()



