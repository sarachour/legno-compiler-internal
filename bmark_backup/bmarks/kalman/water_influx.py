
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
    'meas_noise':0.3,
    'proc_noise':0.1,
    'XL0':0.0,
    'XF0':0.0,
    'P0':1.0,
    'Z0':0.1,
    'flow':-0.1,
    'influx':0.2,
    "one":0.9999
  }
  # water with an unknown fill rate.
  prob = MathProg("KWaterInflux")
  params['Q'] = params['meas_noise']
  params['Rinv'] = 1.0/params['proc_noise']
  params['nRinv'] = -1.0/params['proc_noise']
  params['flow2'] = 2*params['flow']


  dZ = parse_diffeq("{influx}+{flow}*Z", \
                    "Z0", \
                    ":z", \
                    params)

  E = parse_fn("{one}*Z+{one}*(-XL)",params)
  dXL = parse_diffeq("{one}*XF + {flow}*XL + {Rinv}*P11*E", \
                     "XL0",\
                     ":a", \
                     params)

  dXF = parse_diffeq("{Rinv}*P12*E",
                     "XF0",
                     ":b",
                     params)


  dP11 = parse_diffeq("{flow2}*P11 + 2.0*P12 +{Q}+ {nRinv}*P11*P11", \
                      "P0", \
                      ":p11", \
                      params)

  dP12 = parse_diffeq("{flow}*P11 + {one}*P12 +{Q}+ {nRinv}*P11*P12", \
                      "P0", \
                      ":p12", \
                      params)

  dP22 = parse_diffeq("{nRinv}*P12*P12+{Q}", \
                      "P0", \
                      ":p22", \
                      params)



  prob.bind("XL",dXL)
  prob.bind("Z",dZ)
  prob.bind("E",E)
  prob.bind("XF",dXF)
  prob.bind("P11",dP11)
  prob.bind("P12",dP12)
  prob.bind("P22",dP22)
  measure_var(prob,"XL","PROB")

  prob.set_interval("XL",0,2.5)
  prob.set_interval("XF",0,0.5)
  prob.set_interval("P11",0,1.5)
  prob.set_interval("P12",0,1.5)
  prob.set_interval("P22",0,1.5)
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

