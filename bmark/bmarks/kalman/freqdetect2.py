
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
    'W0':0.5,
    'V0':0.0,
    'X0':0.0,
    'Pinit':0.1
  }
  prob = MathProg("kalman-freq2")

 
  params['Q'] = params['meas_noise']
  params['Rinv'] = 1.0/params['proc_noise']
  params['nRinv'] = -params['Rinv']

  ZP,ZV = build_std_bb_sys(prob,1.0,99)
  params['Z'] = ZP

  E = parse_fn("{Rinv}*({Z}+(-X))",params)
  dW = parse_diffeq("P13*E", \
                    "W0", \
                    ':w', \
                    params)
  dV = parse_diffeq("X*(-W) + (P23)*E", \
                    "V0", \
                    ":v", \
                    params)
  dX = parse_diffeq("V + (P33)*E",\
                    "X0", \
                    ":x", \
                    params)

  #square_fun = op.Func(['V'], op.Mult(op.Var('V'),\
  #                                  op.Var('V')))

  dP11 = parse_diffeq("{Q}+{nRinv}*(P13*P13)",
                    "Pinit",
                    ":p11",
                    params)


  dP12 = parse_diffeq("{Q}+P11*(-X)+P13*(-W)+{nRinv}*(P13*P23)",
                   "Pinit",
                    ":p12",
                    params)


  dP13 = parse_diffeq("{Q}+P12 + {nRinv}*(P13*P33)",
                    "Pinit",
                    ":p13",
                    params)

  dP22 = parse_diffeq("{Q}+2.0*(P12*(-X)+P23*(-W)) + {nRinv}*(P23*P23)",
                    "Pinit",
                    ":p22",
                    params)

  dP23 = parse_diffeq("{Q}+P13*(-X) + P33*(-W)+ P22 + {nRinv}*(P23*P33)",
                    "Pinit",
                    ":p23",
                    params)

  dP33 = parse_diffeq("{Q}+2.0*P23 + {nRinv}*(P33*P33)",
                    "Pinit",
                    ":p33",
                    params)




  prob.bind("E",E)
  prob.bind("X",dX)
  prob.bind("V",dV)
  prob.bind("W",dW)
  prob.bind("P11",dP11)
  prob.bind("P12",dP12)
  prob.bind("P13",dP13)
  prob.bind("P22",dP22)
  prob.bind("P23",dP23)
  prob.bind("P33",dP33)

  for cov in ['11','12','13','22','23','33']:
    prob.set_interval("P%s" % cov,-1,1)

  prob.set_interval("X",-2,2)
  prob.set_interval("V",-2,2)
  prob.set_interval("W",-2,2)

  measure_var(prob,"W","FREQSQ")
  prob.set_max_sim_time(200)
  prob.compile()
  menv = menvs.get_math_env('t200')
  return menv,prob


def execute():
  menv,prob = model()
  plot_diffeq(menv,prob)


if __name__ == "__main__":
  execute()


