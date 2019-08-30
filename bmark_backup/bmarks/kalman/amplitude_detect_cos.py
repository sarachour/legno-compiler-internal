
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
    'proc_noise':1.0,
    'one':0.99999,
    'G':0.75,
    'X0':0.0,
    'P0':1.0
  }
  prob = MathProg("KAmplDetectCos")

  params['Q'] = params['meas_noise']
  params['Rinv'] = 1.0/params['proc_noise']
  params['nRinv'] = -1.0/params['proc_noise']
  params['GSQQ'] = params['G']*params['G']*params["Q"]
  build_cos(prob,"0.2",0.2,"Z")

  dX = parse_diffeq("{Rinv}*P*E", \
                    "X0", \
                    ":x", \
                    params)
  E = parse_fn("{one}*Z+{one}*(-X)",params)

  dP = parse_diffeq("{nRinv}*P*P", \
                    "P0", \
                    ":p", \
                    params)

  measure_var(prob,"X","SIG")
  prob.bind("E",E)
  prob.bind("P",dP)
  prob.bind("X",dX)
  prob.set_interval("X",-1.0,1.0)
  prob.set_interval("P",0.0,2.0)
  prob.set_max_sim_time(50)
  prob.compile()
  menv = menvs.get_math_env('t50')
  return menv,prob


def execute():
  menv,prob = model()
  plot_diffeq(menv,prob)


if __name__ == "__main__":
  execute()

