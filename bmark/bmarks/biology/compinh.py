'''
ds
dt = −k1s(eo − c1 − c2) + k−1c1
dc1
dt = k1s(eo − c1 − c2) − (k−1 + k2)c1
dc2
dt = k3(io − c2)(eo − c1 − c2) − k−3c2
'''
if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../"))

from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import math
import bmark.menvs as menvs

def emit(v):
  return op.Emit(op.Mult(op.Const(0.99999), v))


def model():
  prob = MathProg("compinh")
  params = {
    'S0':0.0,
    'A0':0.1,
    'B0':0.3,
    'I0':0.5,
    'E0':0.3,
    'k1f':0.1,
    'k1r':0.1,
    'k2':0.1,
    'k3f':0.1,
    'k3r':0.1
  }
  params['k1rk2'] = params['k1r']+params['k2']
  S = parse_diffeq("{k1f}*S*((-{E0})+A+B) + {k1r}*A", "S0", ":z", params)
  prob.bind("S",S)
  A = parse_diffeq("{k1f}*S*({E0}+(-A)+(-B)) + ({k1rk2})*(-A)", 'A0', \
                   ":y", params)
  prob.bind("A",A)
  B = parse_diffeq("{k3f}*({I0}+(-B))*({E0}+(-A)+(-B))+{k3r}*(-B)", 'B0', \
                   ":z",params)
  prob.bind("B",B)
  prob.set_interval("S",0,0.5)
  prob.set_interval("A",0,0.5)
  prob.set_interval("B",0,0.5)
  prob.bind("COMPLEX", emit(op.Var("S")))
  prob.set_max_sim_time(20)
  prob.compile()
  menv = menvs.get_math_env('t20')
  return menv,prob


def execute():
  menv,prob = model()
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute()
