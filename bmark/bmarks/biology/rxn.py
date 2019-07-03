if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs

def emit(v):
  return op.Emit(op.Mult(op.Const(0.99999), v))

#
def model_dimer_lut():
  # M+M -> D
  # k*2*M^2
  params = {
    'k': 0.05,
    'D0': 0.0,
    'M0': 10.0
  }
  square_fun = op.Func(['V'], op.Mult(op.Var('V'),op.Var('V')))

  prob = MathProg("rxn-dimer-lut")
  params['2k'] = params['k']*2.0
  D = parse_diffeq("{k}*MSQ",'D0',':x',params)
  M = parse_diffeq("-{2k}*MSQ",'M0',':y',params)
  prob.bind("MSQ",op.Call([op.Var('M')], square_fun))
  prob.bind("DIMER", emit(op.Var("D")))
  prob.bind("D",D)
  prob.bind("M",M)
  prob.set_interval("M",0.0,params['M0'])
  prob.set_interval("D",0.0,params["M0"]*0.5+params["D0"])
  prob.compile()
  prob.set_max_sim_time(20)
  menv = menvs.get_math_env('t20')
  return menv,prob

def model_dimer_mult():
  # M+M -> D
  # k*2*M^2
  params = {
    'k': 0.1,
    'D0': 0.1,
    'M0': 1.0
  }
  prob = MathProg("rxn-dimer-mult")
  params['2k'] = params['k']*2.0
  D = parse_diffeq("{k}*M*M",'D0',':x',params)
  M = parse_diffeq("-{2k}*M*M",'M0',':y',params)
  prob.bind("DIMER", emit(op.Var("D")))
  prob.bind("D",D)
  prob.bind("M",M)
  prob.set_interval("M",0.0,params['M0'])
  prob.set_interval("D",0.0,params["M0"]*0.5+params["D0"])
  prob.compile()
  prob.set_max_sim_time(20)
  menv = menvs.get_math_env('t20')
  return menv,prob

def model_dissoc():
  params = {
    'k': 0.3,
    'X0': 1.0,
    'Y0': 0.0,
    'Z0': 1.7
  }
  prob = MathProg("rxn-dissoc")
  X = parse_diffeq("{k}*Z",'X0',':x',params)
  Y = parse_diffeq("{k}*Z",'Y0',':y',params)
  Z = parse_diffeq("{k}*(-Z)",'Z0',':z',params)
  prob.bind("COMP", emit(op.Var("Z")))
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


def model_bidir():
  params = {
    'kf': 0.3,
    'kr': 0.15,
    'X0': 1.0,
    'Y0': 1.0,
    'Z0': 0.0
  }
  prob = MathProg("rxn-bidir")
  X = parse_diffeq("{kf}*(-X)*Y+{kr}*Z",'X0',':x',params)
  Y = parse_diffeq("{kf}*(-X)*Y+{kr}*Z",'Y0',':y',params)
  Z = parse_diffeq("{kf}*X*Y+{kr}*(-Z)",'Z0',':z',params)
  prob.bind("COMP", emit(op.Var("Z")))
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


def model_bimolec():
  params = {
    'k': 0.1,
    'X0': 3.0,
    'Y0': 5.0,
    'Z0': 0.0
  }
  prob = MathProg("rxn-bimolec")
  X = parse_diffeq("{k}*(-X)*Y",'X0',':x',params)
  Y = parse_diffeq("{k}*(-X)*Y",'Y0',':y',params)
  Z = parse_diffeq("{k}*X*Y",'Z0',':z',params)
  prob.bind("COMP", emit(op.Var("Z")))
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
  execute(model_bidir)
  execute(model_dissoc)
  execute(model_dimer_mult)
  execute(model_dimer_lut)
1
