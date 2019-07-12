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
  sin_fun = op.Func(['T'], op.Sin(op.Var('T')))
  cos_fun = op.Func(['T'], op.Cos(op.Var('T')))

  ampl = 0.5
  # position is theta.
  P1,V1 = build_std_bb_sys(prob,ampl,0)
  P2,V2 = build_bb_sys(prob,ampl,0.73,1)
  params = {
    'DEG0' : 0,
    'X0': 0,
    'Y0': 0,
    'P1': P1,
    'P2': P2,
    'one':0.999999
  }
  X = parse_diffeq('({P2})*COS', 'X0',':u', params)
  Y = parse_diffeq('({P2})*SIN', 'Y0',':v', params)
  prob.bind('X',X)
  prob.bind('Y',Y)
  pexpr = op.Var(P1)
  prob.bind('SIN', op.Call([pexpr], sin_fun))
  prob.bind('COS', op.Call([pexpr], cos_fun))
  prob.bind('Rot', emit(op.Var('Y')))
  xrng = 0.5
  yrng = 0.05
  degrng = 0.15
  prob.set_interval("X",-xrng,xrng)
  prob.set_interval("Y",-yrng,yrng)
  # W
  prob.set_max_sim_time(200)
  prob.compile()
  menv = menvs.get_math_env('t200')
  return menv,prob

def execute():
  menv,prob = model()
  plot_diffeq(menv,prob)


if __name__ == "__main__":
  execute()
