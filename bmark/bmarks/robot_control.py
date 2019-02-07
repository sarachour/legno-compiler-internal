from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import math

def model():
  prob = MathProg("robot")
  sin_fun = op.Func(['T'], op.Sin(op.Var('T')))
  cos_fun = op.Func(['T'], op.Cos(op.Var('T')))
  prob.bind('W', op.ExtVar('W'))
  prob.bind('V', op.ExtVar('V'))

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
  return prob
