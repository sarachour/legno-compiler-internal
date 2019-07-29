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

  prob = MathProg("epor")
  params = {
    "p_kt" : 0.0329366,
    "p_Bmax" : 516.0,
    "p_kon" : 0.00010496,
    "p_koff" : 0.0172135,
    "p_ke" : 0.0748267,
    "p_kex" : 0.00993805,
    "p_kdi" : 0.00317871,
    "p_kde" : 0.0164042,
    "EpoEpoR_0": 0.0,
    "EpoEpoRi_0": 0.0,
    'dEpoi_0': 0.0,
    "dEpoe_0": 0.0,
    "EpoR_0": 516.0,
    "Epo_0": 2030.19,
    "one": 0.9999999
  }
  ampls = {
    'EpoR': 516.0,
    'Epo': 2031.0,
    'EpoEpoR': 330.0,
    'EpoEpoRi':516.0,
    'dEpoi':250.0,
    'dEpoe':800
  }
  # reparametrization
  scf = 100.0
  params = {
    "p_kt" : 0.0329366*scf,
    "p_Bmax" : 0.516*scf,
    "p_kon" : 0.00010496*scf,
    "p_koff" : 0.0172135*scf,
    "p_ke" : 0.0748267*scf,
    "p_kex" : 0.00993805*scf,
    "p_kdi" : 0.00317871*scf,
    "p_kde" : 0.0164042*scf,
    "EpoEpoR_0": 0.0,
    "EpoEpoRi_0": 0.0,
    'dEpoi_0': 0.0,
    "dEpoe_0": 0.0,
    "EpoR_0": 0.5160,
    "Epo_0": 2.0319,
    "one": 0.9999999
  }
  ampls = {
    'EpoR': 5.160,
    'Epo': 2.0310,
    'EpoEpoR': 0.3300,
    'EpoEpoRi':0.5160,
    'dEpoi':0.2500,
    'dEpoe':0.800
  }
  ic = lambda v: "%s_0" % v
  handle = lambda v: ":%s" % v


  v,e = "rr_46","{p_koff}*EpoEpoR+{p_kex}*EpoEpoRi"
  EXPR = parse_fn(e,params)
  prob.bind(v,EXPR)

  params['p_kt_Bmax'] = params['p_kt'] + params['p_Bmax']
  v,e = "EpoR","{one}*rr_46 + {p_kt_Bmax} + ({p_kt} + {p_kon}*Epo)*(-EpoR)"
  ampl = ampls[v]
  EXPR = parse_diffeq(e,ic(v),handle(v),params)
  prob.bind(v,EXPR)
  prob.set_interval(v,0.0,ampl)

  v,e= "Epo","{one}*rr_46 + {p_kon}*EpoR*(-Epo)"
  ampl = ampls[v]
  EXPR = parse_diffeq(e,ic(v),handle(v),params)
  prob.bind(v,EXPR)
  prob.set_interval(v,0.0,ampl)

  params['p_koff_ke'] = params['p_koff'] + params['p_ke']
  v,e = "EpoEpoR","{p_kon}*Epo*EpoR + {p_koff_ke}*(-EpoEpoR)"
  ampl = ampls[v]
  EXPR = parse_diffeq(e,ic(v),handle(v),params)
  prob.bind(v,EXPR)
  prob.set_interval(v,0.0,ampl)

  params['p_kex_kdi_kde'] = params['p_kex'] + params['p_kdi'] + params['p_kde']
  v,e= "EpoEpoRi","{p_ke}*EpoEpoR + {p_kex_kdi_kde}*(-EpoEpoRi)"
  ampl = ampls[v]
  EXPR = parse_diffeq(e,ic(v),handle(v),params)
  prob.bind(v,EXPR)
  prob.set_interval(v,0.0,ampl)

  v,e= "dEpoi","{p_kdi}*EpoEpoRi"
  EXPR = parse_diffeq(e,ic(v),handle(v),params)
  ampl = ampls[v]
  prob.bind(v,EXPR)
  prob.set_interval(v,0.0,ampl)

  v,e= "dEpoe","{p_kde}*EpoEpoRi"
  EXPR = parse_diffeq(e,ic(v),handle(v),params)
  ampl = ampls[v]
  prob.bind(v,EXPR)
  prob.set_interval(v,0.0,ampl)

  measure_var(prob,'EpoEpoRi','EPOEPORI')
  prob.set_max_sim_time(200)
  prob.compile()
  menv = menvs.get_math_env('t200')

  return menv,prob

def execute():
  menv,prob = model()
  plot_diffeq(menv,prob)



if __name__ == "__main__":
  execute()
