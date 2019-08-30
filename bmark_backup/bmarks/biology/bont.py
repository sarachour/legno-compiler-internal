if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))

from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import math
import bmark.menvs as menvs



def model():
  prob = MathProg("bont")
  scf = 1.0
  scf2 = 3.0
  # original set of parameters
  params = {
    'r_endo_kT': 0.141,
    'r_trans_kL': 0.013,
    'r_bind_kB': 0.058,
    'tenB0': 1.0,
    'freeB0': 1.0,
    'bndB0' : 0.0,
    'transB0': 0.0,
    'lyticB0': 0.0
  }
  # reparametrization
  params = {
    'r_endo_kT': 0.541,
    'r_trans_kL': 0.541,
    'r_bind_kB': 0.541,
    'tenB0': 1.0,
    'freeB0': 1.0,
    'bndB0' : 0.0,
    'transB0': 0.0,
    'lyticB0': 0.0
  }
  ic = lambda v: "%s0" % v
  handle = lambda v: ":%s" % v

  v,e = 'tenB','{r_trans_kL}*(-transB)'
  EXPR = parse_diffeq(e,ic(v),handle(v),params)
  prob.bind(v,EXPR)
  prob.set_interval(v,-1.0,1.0)

  v,e = 'freeB','{r_bind_kB}*(-freeB)'
  EXPR = parse_diffeq(e,ic(v),handle(v),params)
  prob.bind(v,EXPR)
  prob.set_interval(v,-1.0,1.0)

  v,e = 'bndB','{r_bind_kB}*(-freeB) + {r_endo_kT}*(-bndB)'
  EXPR = parse_diffeq(e,ic(v),handle(v),params)
  prob.bind(v,EXPR)
  prob.set_interval(v,-1.0,1.0)

  v,e = 'transB','{r_endo_kT}*bndB + {r_trans_kL}*(-transB)'
  EXPR = parse_diffeq(e,ic(v),handle(v),params)
  prob.bind(v,EXPR)
  prob.set_interval(v,-1.0,1.0)

  v,e = 'lyticB','{r_trans_kL}*transB'
  EXPR = parse_diffeq(e,ic(v),handle(v),params)
  prob.bind(v,EXPR)
  prob.set_interval(v,-1.0,1.0)

  measure_var(prob,'transB','MTRANSB')
  prob.set_max_sim_time(20)
  prob.compile()
  menv = menvs.get_math_env('t20')
  return menv,prob


def execute():
  menv,prob = model()
  plot_diffeq(menv,prob)



if __name__ == "__main__":
  execute()
