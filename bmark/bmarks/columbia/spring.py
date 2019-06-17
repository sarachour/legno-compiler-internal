if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs

def model():
  params = {
    'k1': 0.5,
    'k2': 0.5,
    'k3': 0.5,
    'cf': 0.15,
    'PA0': 2,
    'VA0': 0,
    'PB0': -1,
    'VB0': 0,
    'one':0.9999
  }
  params['k1_k2'] = params['k1'] + params['k2']
  params['k2_k3'] = params['k3'] + params['k2']

  prob = MathProg("spring")
  #prob.set_digital_snr(15.0)
  spec_fun = op.Func(['V'], op.Mult(op.Sgn(op.Var('V')),\
                                    op.Sqrt(op.Abs(op.Var('V')))))
  PA = parse_diffeq('{one}*VA', 'PA0', ':a', params)

  VA = parse_diffeq('{k2}*FPB+{k1_k2}*(-FPA)+{cf}*(-VA)', 'VA0', ':b', params)

  PB = parse_diffeq('{one}*VB', 'PB0', ':c', params)

  VB = parse_diffeq('{k2}*FPA+{k2_k3}*(-FPB)+{cf}*(-VB)', 'VB0', ':d', params)

  FPA = op.Call([op.Var('PA')],spec_fun)
  FPB = op.Call([op.Var('PB')],spec_fun)
  prob.bind('PA', PA)
  prob.bind('PB', PB)
  prob.bind('VA', VA)
  prob.bind('VB', VB)
  prob.bind('FPA', FPA)
  prob.bind('FPB', FPB)
  abnd = 2
  bbnd = 1
  prob.set_interval("PA",-2,2)
  prob.set_interval("PB",-1.5,1.5)
  prob.set_interval("VA",-2,2)
  prob.set_interval("VB",-2,2)
  prob.set_max_sim_time(20)
  prob.bind('PosA', op.Emit(op.Var('PA'),loc="A0"))
  prob.compile()

  menv = menvs.get_math_env('t20')
  return menv,prob

def execute():
  menv,prob = model()
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute()
