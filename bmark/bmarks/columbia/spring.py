if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs

def model(nonlinear=False):
  k = 0.5
  cf= 0.15
  params = {
    'k1': k,
    'k2': k,
    'k3': k,
    'cf': -cf,
    'PA0': 2.0,
    'VA0': 0,
    'PB0': -1.0,
    'VB0': 0,
    'one':0.9999
  }
  params['k1_k2'] = -(params['k1'] + params['k2'])*0.999
  params['k2_k3'] = -(params['k3'] + params['k2'])*0.999

  if nonlinear:
    prob = MathProg("spring-nl")
  else:
    prob = MathProg("spring")

  #prob.set_digital_snr(15.0)
  
  PA = parse_diffeq('VA', 'PA0', ':a', params)
  if nonlinear:
    VA = parse_diffeq('{k2}*FPB+{k1_k2}*(FPA)+{cf}*(VA)', 'VA0', ':b', params)
  else:
    VA = parse_diffeq('{k2}*PB+{k1_k2}*(PA)+{cf}*(VA)', 'VA0', ':b', params)

  PB = parse_diffeq('VB', 'PB0', ':c', params)
  if nonlinear:
    VB = parse_diffeq('{k2}*FPA+{k2_k3}*(FPB)+{cf}*(VB)', 'VB0', ':d', params)
  else:
    VB = parse_diffeq('{k2}*PA+{k2_k3}*(PB)+{cf}*(VB)', 'VB0', ':d', params)

  prob.bind('PA', PA)
  prob.bind('PB', PB)
  prob.bind('VA', VA)
  prob.bind('VB', VB)
  if nonlinear:
    spec_fun = op.Func(['V'], op.Mult(op.Sgn(op.Var('V')),\
                                      op.Sqrt(op.Abs(op.Var('V')))))
    #spec_fun = op.Func(['V'], op.Var('V'))

    FPA = op.Call([op.Var('PA')],spec_fun)
    FPB = op.Call([op.Var('PB')],spec_fun)
    prob.bind('FPA', FPA)
    prob.bind('FPB', FPB)
  # increasing the interval of the velocity helped.
  pbnd = 2.5
  vbnd = 2.5
  prob.set_interval("PA",-pbnd,pbnd)
  prob.set_interval("PB",-pbnd,pbnd)
  prob.set_interval("VA",-vbnd,vbnd)
  prob.set_interval("VB",-vbnd,vbnd)
  prob.set_max_sim_time(20)
  #measure_var(prob,"PA","PosA")
  #measure_var(prob,"FPA","FuncA")
  if nonlinear:
    prob.bind('PosB', op.Emit(op.Var('PB'),loc="A0"))
  else:
    prob.bind('PosA', op.Emit(op.Var('PA'),loc="A0"))
  prob.compile()

  menv = menvs.get_math_env('t20')
  return menv,prob

def execute(nonlinear=False):
  menv,prob = model(nonlinear)
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute(nonlinear=False)
  execute(nonlinear=True)
