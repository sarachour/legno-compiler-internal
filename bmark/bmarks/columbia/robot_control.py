if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
from bmark.bmarks.other.bbsys import \
  build_bb_sys, \
  build_std_bb_sys
import math
import bmark.menvs as menvs

def emit(v):
  return op.Emit(op.Mult(op.Const(0.99999), v), loc="A0")


def model():
  prob = MathProg("robot")
  sin_fun = op.Func(['T'], op.Sin(op.Mult(op.Const(math.pi), \
                                          op.Var('T'))))
  cos_fun = op.Func(['T'], op.Cos(op.Mult(op.Const(math.pi), \
                                          op.Var('T'))))

  ampl = 1.0
  # position is theta.
  P1,_ = build_std_bb_sys(prob,ampl,0)
  inpgen1 = op.Func(['T'],op.RandFun(op.Var('T'),255,123213))
  inpgen2 = op.Func(['T'],op.RandFun(op.Var('T'),255,4324324))

  #P2,V2 = build_bb_sys(prob,ampl,0.73,1)
  params = {
    'DEG0' : 0,
    'X0': 0,
    'Y0': 0,
    'P1': P1,
    'one':0.999999,
    'decay':0.2
  }
  # without decay: drift (drifts negative over time.)
  # with decay:

  X = parse_diffeq('V*COS-{decay}*X', 'X0',':u', params)
  Y = parse_diffeq('V*SIN-{decay}*Y', 'Y0',':v', params)
  pexpr = op.Var(P1)
  prob.bind('W', op.Call([pexpr], inpgen1))
  prob.bind('V', op.Call([pexpr], inpgen2))
  prob.bind('X',X)
  prob.bind('Y',Y)
  pexpr = op.Var('W')
  prob.bind('SIN', op.Call([pexpr], sin_fun))
  prob.bind('COS', op.Call([pexpr], cos_fun))
  prob.bind('Rot', emit(op.Var('X')))
  xrng = 1.0
  yrng = 1.0
  prob.set_interval("X",-xrng,xrng)
  prob.set_interval("Y",-yrng,yrng)
  # W
  prob.set_max_sim_time(50)
  prob.compile()
  menv = menvs.get_math_env('t50')
  return menv,prob

def execute():
  menv,prob = model()
  plot_diffeq(menv,prob)


if __name__ == "__main__":
  execute()
