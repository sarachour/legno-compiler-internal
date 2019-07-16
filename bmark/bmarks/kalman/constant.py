if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))


from bmark.bmarks.common import *
from lang.prog import MathProg
from ops import op, opparse
import bmark.menvs as menvs


def model():
  params = {
    'meas_noise':0.02,
    'proc_noise':0.02,
    'mean':0.5,
  }
  params['meas_noise_inv'] = 1.0/params['meas_noise']
  params['X0'] = 0.25
  params['P0'] = 0.3

  prob = MathProg("kalman-const")

  dX = parse_diffeq("{meas_noise_inv}*P*(Z-X)","X0", \
                    ":a",params)
  dP = parse_diffeq("{proc_noise}-{meas_noise_inv}*P*P","P0", \
                    ":b",params)
  Z = parse_fn("{mean}",params)

  prob.bind("X",dX)
  prob.bind("P",dP)
  prob.bind("Z",Z)
  measure_var(prob,"X", "OUT")
  prob.set_interval("X",0,1.0)
  prob.set_interval("P",0,0.3)
  prob.set_interval("Z",0,1.0)
  prob.set_max_sim_time(50)
  prob.compile()
  menv = menvs.get_math_env('t50')
  return menv,prob



def execute():
  menv,prob = model()
  plot_diffeq(menv,prob)


if __name__ == "__main__":
  execute()


