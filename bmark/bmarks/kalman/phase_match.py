if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))

from bmark.bmarks.common import *
from lang.prog import MathProg
from ops import op, opparse
import bmark.menvs as menvs
from bmark.bmarks.other.closed_form import *
import math


'''
matches sin wave with a different phase

'''
def model():
  params = {
    'meas_noise':0.3,
    'proc_noise':0.5,
    'X0':1.0,
    'V0':0.0,
    'P0':1.0,
    'one':0.9999
  }
  prob = MathProg("KPhaseMatch")
  build_sin(prob,"1.0",1.0,"Z")
  params['Q'] = params['meas_noise']
  params['Rinv'] = 1.0/params['proc_noise']
  params['nRinv'] = -1.0/params['proc_noise']

  E = parse_fn("{one}*Z+{one}*(-X)",params)
  dX = parse_diffeq("{one}*V + {Rinv}*P11*E", \
                    "X0", \
                    ":x", \
                    params)
  dV = parse_diffeq("{one}*(-X) + {Rinv}*P12*E", \
                    "V0", \
                    ":v", \
                    params)

  dP11 = parse_diffeq("2.0*P12 + {Q} + {nRinv}*P11*P11", \
                      "P0", \
                      ":p11", \
                      params)
  dP12 = parse_diffeq("{one}*P22+{one}*(-P11) +{Q} + {nRinv}*P11*P12", \
                      "P0", \
                      ":p12", \
                      params)
  dP22 = parse_diffeq("2.0*(-P12) + {Q} + {nRinv}*P12*P12", \
                      "P0", \
                      ":p22", \
                      params)

  measure_var(prob,"X","MODEL")
  prob.bind("E",E)
  prob.bind("X",dX)
  prob.bind("V",dV)
  prob.bind("P11",dP11)
  prob.bind("P12",dP12)
  prob.bind("P22",dP22)
  prob.set_interval("X",-1.0,1.0)
  prob.set_interval("V",-1.0,1.0)
  prob.set_interval("P11",0.0,1.0)
  prob.set_interval("P12",0.0,1.0)
  prob.set_interval("P22",0.0,1.0)
  prob.compile()
  prob.set_max_sim_time(50)
  menv = menvs.get_math_env('t50')
  return menv,prob



def execute():
  menv,prob = model()
  plot_diffeq(menv,prob)


if __name__ == "__main__":
  execute()


