from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *


def model():
  params = {
    'k1': 0.5,
    'k2': 0.5,
    'k3': 0.5,
    'cf': 0.15,
    'PA0': 2,
    'VA0': 0,
    'PB0': -1,
    'VB0': 0
  }
  params['k1_k2'] = params['k1'] + params['k2']
  params['k2_k3'] = params['k3'] + params['k2']

  prob = MathProg("spring")
  spec_fun = op.Func(['V'], op.Mult(op.Sgn(op.Var('V')),op.Sqrt(op.Abs(op.Var('V')))))
  PA = parse_diffeq('VA', 'PA0', ':a', params)
  VA = parse_diffeq('k2*FPB-k1_k2*FPA-cf*VA', 'VA0', ':b', params)
  PB = parse_diffeq('VB', 'PB0', ':c', params)
  VB = parse_diffeq('k2*FPA-k2_k3*FPB-cf*VB', 'VB0', ':d', params)
  FPA = op.Call([op.Var('VA')],spec_fun)
  FPB = op.Call([op.Var('VB')],spec_fun)
  prob.bind('PA', PA)
  prob.bind('PB', PB)
  prob.bind('VA', VA)
  prob.bind('VB', VB)
  prob.bind('FPA', FPA)
  prob.bind('FPB', FPB)
  abnd = 2
  bbnd = 1
  prob.set_interval("PA",-abnd,abnd)
  prob.set_interval("PB",-bbnd,bbnd)
  prob.set_interval("VA",-abnd,abnd)
  prob.set_interval("VB",-bbnd,bbnd)

  prob.bind('PosA', op.Emit(op.Var('PA')))
  prob.compile()
  return prob
