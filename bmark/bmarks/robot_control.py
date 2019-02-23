if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import math
import bmark.menvs as menvs

def model():
  prob = MathProg("robot")
  sin_fun = op.Func(['T'], op.Sin(op.Var('T')))
  cos_fun = op.Func(['T'], op.Cos(op.Var('T')))

  params = {
    'DEG0' : 0,
    'X0': 0,
    'Y0': 0
  }
  DEG = parse_diffeq('W', 'DEG0', ':t', params)
  X = parse_diffeq('V*COS', 'X0',':u', params)
  Y = parse_diffeq('V*SIN', 'Y0',':v', params)
  prob.bind('DEG',DEG)
  prob.bind('X',X)
  prob.bind('Y',Y)
  prob.bind('W', op.ExtVar('I1'))
  prob.bind('V', op.ExtVar('I2'))
  prob.bind('SIN', op.Call([op.Var('DEG')], sin_fun))
  prob.bind('COS', op.Call([op.Var('DEG')], cos_fun))
  prob.bind('Rot', op.Emit(op.Var('Y')))
  prob.set_interval("DEG",-2*math.pi,2*math.pi)
  pos = 100
  prob.set_interval("W",-0.1,0.1)
  prob.set_interval("V",-1,1)
  prob.set_bandwidth("V",10)
  prob.set_bandwidth("W",10)
  prob.set_interval("X",-pos,pos)
  prob.set_interval("Y",-pos,pos)
  prob.compile()
  menv = menvs.get_math_env('t2ksin2')
  return menv,prob

def execute():
  menv,prob = model()
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute()
