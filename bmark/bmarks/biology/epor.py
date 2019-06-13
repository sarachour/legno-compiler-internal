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

  ic = lambda v: "%s_0" % v
  handle = lambda v: ":%s" % v


  v,e = "rr_46","{p_koff}*EpoEpoR+{p_kex}*EpoEpoRi"
  EXPR = parse_fn(e,params)
  prob.bind(v,EXPR)

  params['p_kt_Bmax'] = params['p_kt'] + params['p_Bmax']
  v,e,ampl = "EpoR","{one}*rr_46 + {p_kt_Bmax} + ({p_kt} + {p_kon}*Epo)*(-EpoR)",516.0
  EXPR = parse_diffeq(e,ic(v),handle(v),params)
  prob.bind(v,EXPR)
  prob.set_interval(v,0.0,ampl)

  v,e,ampl = "Epo","{one}*rr_46 + {p_kon}*EpoR*(-Epo)",2031
  EXPR = parse_diffeq(e,ic(v),handle(v),params)
  prob.bind(v,EXPR)
  prob.set_interval(v,0.0,ampl)

  params['p_koff_ke'] = params['p_koff'] + params['p_ke']
  v,e,ampl = "EpoEpoR","{p_kon}*Epo*EpoR + {p_koff_ke}*(-EpoEpoR)",330
  EXPR = parse_diffeq(e,ic(v),handle(v),params)
  prob.bind(v,EXPR)
  prob.set_interval(v,0.0,ampl)

  params['p_kex_kdi_kde'] = params['p_kex'] + params['p_kdi'] + params['p_kde']
  v,e,ampl = "EpoEpoRi","{p_ke}*EpoEpoR + {p_kex_kdi_kde}*(-EpoEpoRi)",516
  EXPR = parse_diffeq(e,ic(v),handle(v),params)
  prob.bind(v,EXPR)
  prob.set_interval(v,0.0,ampl)

  v,e,ampl = "dEpoi","{p_kdi}*EpoEpoRi",250
  EXPR = parse_diffeq(e,ic(v),handle(v),params)
  prob.bind(v,EXPR)
  prob.set_interval(v,0.0,ampl)

  v,e,ampl = "dEpoe","{p_kde}*EpoEpoRi",800
  EXPR = parse_diffeq(e,ic(v),handle(v),params)
  prob.bind(v,EXPR)
  prob.set_interval(v,0.0,ampl)

  measure_var(prob,'EpoEpoRi','EPO_EPORI')
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
