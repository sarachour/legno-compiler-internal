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
    'proc_noise':0.05,
    'X0':1.0,
    'P0':0.9,
    'one':0.9999
  }
  prob = MathProg("KShiftModulate")

  '''
  amplitude modulation of a constant signal.
  '''
  params['Q'] = params['meas_noise']
  params['Rinv'] = 1.0/params['proc_noise']
  params['nRinv'] = -1.0/params['proc_noise']

  build_cos(prob,"0.2",math.sqrt(0.2),"DATA")
  build_cos(prob,"2.0",math.sqrt(2.0),"CARRIER")
  #data_fn = op.Func(['V'], op.Add(
  #  op.Const(0.7),
  #  op.Mult(op.Sgn(op.Var('V')), op.Const(0.3)) \
  #))

  #DATA = op.Call([op.Var("DFREQ")], data_fn)
  # Z = DATA+CARRIER
  E = parse_fn("{one}*DATA+CARRIER+{one}*(-X)+(-CARRIER)", \
               params)
  dX = parse_diffeq("{Rinv}*P*E", \
                    "X0", \
                    ":x", \
                    params)

  dP = parse_diffeq("{Q}+{nRinv}*P*P", \
                    "P0", \
                    ":p", \
                    params)


  measure_var(prob,"X","STATE")

  prob.bind("E",E)
  prob.bind("P",dP)
  prob.bind("X",dX)
  prob.set_interval("X",-2.0,2.0)
  prob.set_interval("P",0.0,1.0)
  prob.set_max_sim_time(50)
  prob.compile()
  menv = menvs.get_math_env('t50')
  return menv,prob



def execute():
  menv,prob = model()
  plot_diffeq(menv,prob)


if __name__ == "__main__":
  execute()



