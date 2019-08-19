
if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))


from bmark.bmarks.common import *
from lang.prog import MathProg
from ops import op, opparse
import bmark.menvs as menvs
from bmark.bmarks.other.bbsys import build_std_bb_sys
from bmark.bmarks.other.closed_form \
  import build_sin, build_cos, build_sin_and_cos

def model():
  params = {
    'meas_noise':0.01,
    'proc_noise':0.99999,
    'W0':0.707,
    'P0':0.1,
    'one':0.9999
  }
 
  prob = MathProg("kalman-freq-small")
  params['Rinv'] = 1.0/params['proc_noise']
  params['nRinv'] = -params['Rinv']
  params['Q'] = params['meas_noise']

  build_cos(prob,"0.5",0.5,"BB")
  build_sin_and_cos(prob, \
                    "WSQ","W", \
                    3.0, \
                    "COSW","WSINW",
                    normalize=False)

  WSq = parse_fn("W*W", params)
  SINW2 = parse_fn("WSINW*WSINW",params)

  dW = parse_diffeq('{nRinv}*P*WSINW*({one}*BB-{one}*COSW)', \
                    "W0",
                    ":w",
                    params)

  #{Q} + {nRinv}*WSINW2*P*P"
  dP = parse_diffeq("{nRinv}*WSINW2*P*P", \
                    "P0", \
                    ":p", \
                    params)

  prob.bind("W",dW)
  prob.bind("P",dP)
  prob.bind("WSQ",WSq)
  prob.bind("WSINW2",SINW2)

  prob.set_interval("W",-10,10)
  prob.set_interval("P",-0.3,0.3)

  measure_var(prob,"WSQ","FREQ")
  prob.set_max_sim_time(200)
  prob.compile()
  menv = menvs.get_math_env('t200')
  return menv,prob


def execute():
  menv,prob = model()
  plot_diffeq(menv,prob)


def execute():
  menv,prob = model()
  plot_diffeq(menv,prob)


if __name__ == "__main__":
  execute()


