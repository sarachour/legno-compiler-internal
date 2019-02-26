if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs


#
def model_dimer_mult():
  raise NotImplementedError

def model_dimer_lut():
  raise NotImplementedError

def model_dissoc():
  params = {
    'k': 0.1,
    'X0': 0.1,
    'Y0': 0.0,
    'Z0': 0.7
  }
  prob = MathProg("rxn-dissoc")
  X = parse_diffeq("{k}*Z",'X0',':x',params)
  Y = parse_diffeq("{k}*Z",'Y0',':y',params)
  Z = parse_diffeq("{k}*(-Z)",'Z0',':z',params)
  prob.bind("COMP", op.Emit(op.Var("Z")))
  prob.bind("X",X)
  prob.bind("Y",Y)
  prob.bind("Z",Z)
  prob.set_interval("X",0.0,params['X0']+params['Z0'])
  prob.set_interval("Y",0.0,params['Y0']+params['Z0'])
  prob.set_interval("Z",0.0,params['Z0'])
  prob.set_max_sim_time(20)
  prob.compile()
  menv = menvs.get_math_env('t20')
  return menv,prob


def model_bimolec():
  params = {
    'k': 0.1,
    'X0': 0.3,
    'Y0': 0.5,
    'Z0': 0.0
  }
  prob = MathProg("rxn-bimolec")
  X = parse_diffeq("{k}*(-X)*Y",'X0',':x',params)
  Y = parse_diffeq("{k}*(-X)*Y",'Y0',':y',params)
  Z = parse_diffeq("{k}*X*Y",'Z0',':z',params)
  prob.bind("COMP", op.Emit(op.Var("Z")))
  prob.bind("X",X)
  prob.bind("Y",Y)
  prob.bind("Z",Z)
  prob.set_interval("X",0.0,params['X0'])
  prob.set_interval("Y",0.0,params['Y0'])
  ZMAX = min(params['Y0'],params['X0'])+params['Z0']
  prob.set_interval("Z",0.0,ZMAX)
  prob.set_max_sim_time(20)
  prob.compile()
  menv = menvs.get_math_env('t20')
  return menv,prob


def execute(model_fun):
  menv,prob =model_fun()
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute(model_bimolec)
  execute(model_dissoc)
1
