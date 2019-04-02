if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
from bmark.bmarks.bbsys import build_bb_sys
import math
import bmark.menvs as menvs

def emit(v):
  return op.Emit(op.Mult(op.Const(0.99999), v))


def model():
  prob = MathProg("robot")
  sin_fun = op.Func(['T'], op.Sin(op.Var('T')))
  cos_fun = op.Func(['T'], op.Cos(op.Var('T')))

  ampl,freq = 0.3,0.25
  W,V = build_bb_sys(prob,ampl,freq,0)
  params = {
    'DEG0' : 0,
    'X0': 0,
    'Y0': 0,
    'W': W,
    'V': V,
    'one':0.999999
  }
  DEG = parse_diffeq('{one}*{W}', 'DEG0', ':t', params)
  X = parse_diffeq('{one}*{V}*COS', 'X0',':u', params)
  Y = parse_diffeq('{one}*{V}*SIN', 'Y0',':v', params)
  prob.set_default_snr(2.5)
  prob.set_snr('X',5)
  prob.set_snr('Y',5)
  prob.set_snr('DEG',2)
  prob.set_snr('Rot',5)
  prob.bind('DEG',DEG)
  prob.bind('X',X)
  prob.bind('Y',Y)
  prob.bind('SIN', op.Call([op.Var('DEG')], sin_fun))
  prob.bind('COS', op.Call([op.Var('DEG')], cos_fun))
  prob.bind('Rot', emit(op.Var('Y')))
  pos = 1.0
  xrng = 1.5
  yrng = 2.5
  degrng = 0.5
  prob.set_interval("X",-xrng,xrng)
  prob.set_interval("Y",0,yrng)
  prob.set_interval("DEG",-degrng,degrng)
  # W
  prob.set_max_sim_time(200)
  prob.compile()
  menv = menvs.get_math_env('t200')
  return menv,prob

def execute():
  menv,prob = model()
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute()
