
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
    'proc_noise':0.1,
    'W0':1.0,
    'V0':0.0,
    'X0':1.0,
    'Pinit':0.1
  }
  prob = MathProg("kalman-freq")

  params['Q'] = params['meas_noise']
  params['Rinv'] = 1.0/params['proc_noise']
  params['nRinv'] = -params['Rinv']

  ZP,ZV = build_std_bb_sys(prob,1.0,99)
  EV = parse_fn("%s-V" % ZV,params)
  EX = parse_fn("%s-X" % ZP,params)

  dW = parse_diffeq("{Rinv}*(P2*EV+P3*EX)", \
                    "W0", \
                    ':a', \
                    params)
  dV = parse_diffeq("(-W)*X+{Rinv}*(P5*EV+P6*EX)", \
                    'V0', \
                    ':b', \
                    params)
  dX = parse_diffeq("V+{Rinv}*(P8*EV+P9*EX)", \
                    'X0', \
                    ':c', \
                    params)

  dP1 = parse_diffeq("{Q}+{nRinv}*(P2*P4 + P3*P7)", \
                     "Pinit", \
                     ":p1", \
                     params)
  dP2 = parse_diffeq("V*(-P1)+W*(-P2)+{Q}+{nRinv}*(P2*P5 + P3*P8)", \
                     "Pinit", \
                     ":p2", \
                     params)
  dP3 = parse_diffeq("P2 + {Q} + {nRinv}*(P2*P6+P3*P9)", \
                     "Pinit", \
                     ":p3", \
                     params)

  dP4 = parse_diffeq("V*(-P2) + W*(-P4) + {Q} + {nRinv}*(P4*P5 + P6*P7)", \
                     "Pinit", \
                     ":p4", \
                     params)
  dP5 = parse_diffeq("V*((-P2)+(-P4)) + W*((-P5)+(-P5)) + {Q} + {nRinv}*(P5*P5 + P6*P8)", \
                     "Pinit", \
                     ":p5", \
                     params)
  dP6 = parse_diffeq("V*(-P3) + W*(-P6) + P5 + {Q} + {nRinv}*(P5*P6 + P6*P9)", \
                     "Pinit", \
                     ":p6", \
                     params)

  dP7 = parse_diffeq("P4 + {Q} + {nRinv}*(P8*P4 + P7*P9)", \
                     "Pinit", \
                     ":p7", \
                     params)
  dP8 = parse_diffeq("P5 + V*(-P7) + W*(-P8) + {Q} + {nRinv}*(P5 + P9)*P8", \
                     "Pinit", \
                     ":p8", \
                     params)
  dP9 = parse_diffeq("P6 + P8 + {Q} + {nRinv}*(P8*P6 + P9*P9)", \
                     "Pinit", \
                     ":p9", \
                     params)

  prob.bind("X",dX)
  prob.bind("W",dW)
  prob.bind("V",dV)
  prob.bind("EX",EX)
  prob.bind("EV",EV)
  prob.bind("P1",dP1)
  prob.bind("P2",dP2)
  prob.bind("P3",dP3)
  prob.bind("P4",dP4)
  prob.bind("P5",dP5)
  prob.bind("P6",dP6)
  prob.bind("P7",dP7)
  prob.bind("P8",dP8)
  prob.bind("P9",dP9)

  for cov in range(1,10):
    prob.set_interval("P%d" % cov,-1,1)
  prob.set_interval("X",-1,1)
  prob.set_interval("V",-1,1)
  prob.set_interval("W",-1,1)

  prob.set_max_sim_time(50)
  prob.compile()
  menv = menvs.get_math_env('t50')
  return menv,prob



def execute():
  menv,prob = model()
  plot_diffeq(menv,prob)


if __name__ == "__main__":
  execute()

