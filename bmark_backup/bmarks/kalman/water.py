
if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))

from bmark.bmarks.common import *
from lang.prog import MathProg
from ops import op, opparse
import bmark.menvs as menvs
from bmark.bmarks.other.bbsys import build_std_bb_sys

def model():
  params = {
    'meas_noise':0.0,
    'proc_noise':1.0,
    'X0':1.0,
    'P0':1.0,
    'Z0':0.1,
    'flow':-0.1,
    'influx':0.2,
    'Pinit':1.0
  }
  prob = MathProg("Kwater")
  params['2Flow'] = 2*params['flow']

  params['Q'] = params['meas_noise']
  params['Rinv'] = 1.0/params['proc_noise']
  params['nRinv'] = -1.0/params['proc_noise']

  dZ = parse_diffeq("{influx}+{flow}*Z", \
                    "Z0", \
                    ":b", \
                    params)

  dX = parse_diffeq("U+{flow}*X+{Rinv}*P*(Z-X)", \
                    "X0", \
                    ":a", \
                    params)
  PH = parse_fn("P*{flow}",params)
  U = parse_fn("{influx}",params)
  dP = parse_diffeq("{2Flow}*P +{Q}+{nRinv}*PH*PH", \
                    "P0",\
                    ":b", \
                    params)


  prob.bind("X",dX)
  prob.bind("P",dP)
  prob.bind("U",U)
  prob.bind("PH",PH)
  prob.bind("Z",dZ)
  measure_var(prob,"X","PROB")

  prob.set_interval("X",0,2.5)
  prob.set_interval("P",0,1)
  prob.set_interval("U",0,0.2)
  prob.set_interval("Z",0,2.5)

  prob.set_max_sim_time(50)
  prob.compile()
  menv = menvs.get_math_env('t50')
  return menv,prob

def execute():
  menv,prob = model()
  plot_diffeq(menv,prob)


if __name__ == "__main__":
  execute()

