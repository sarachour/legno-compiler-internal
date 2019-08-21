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
    'meas_noise':0.3,
    'proc_noise':0.1,
    'X0':1.0,
    'P0':1.0,
    'one':0.9999
  }
  prob = MathProg("KAmplModulate")

  '''
  amplitude modulation of a constant signal.
  '''
  params['Q'] = params['meas_noise']
  params['Rinv'] = 1.0/params['proc_noise']
  params['nRinv'] = -1.0/params['proc_noise']

  build_cos(prob,"0.2",math.sqrt(0.2),"DATA")
  build_cos(prob,"1.0",math.sqrt(1.0),"CARRIER")

  PCAR = parse_fn("P*CARRIER",params)
  Z = op.Mult( \
               op.Var("DATA"), \
               op.Var("CARRIER") \
  )
  E = parse_fn("DATA*CARRIER+{one}*(-X)*CARRIER",params)
  dX = parse_diffeq("{Rinv}*P*CARRIER*E", \
                    "X0", \
                    ":x", \
                    params)

  T00 = parse_fn("CARRIER*CARRIER",params)
  T01 = parse_fn("P*P",params)
  T1 = parse_fn("T00*T01",params)
  dP = parse_diffeq("{Q}+{nRinv}*((P*P)*(CARRIER*CARRIER))", \
                    "P0", \
                    ":p", \
                    params)


  measure_var(prob,"P","PROB")

  prob.bind("T00",T00)
  prob.bind("T01",T01)
  prob.bind("T1",T1)
  prob.bind("E",E)
  prob.bind("P",dP)
  prob.bind("Z",Z)
  prob.bind("X",dX)
  prob.set_interval("X",-2.0,2.0)
  prob.set_interval("P",0.0,1.2)
  prob.set_max_sim_time(50)
  prob.compile()
  menv = menvs.get_math_env('t50')
  return menv,prob



def execute():
  menv,prob = model()
  plot_diffeq(menv,prob)


if __name__ == "__main__":
  execute()



