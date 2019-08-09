
if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))


from bmark.bmarks.common import *
from lang.prog import MathProg
from ops import op, opparse
import bmark.menvs as menvs


def build_sin_and_cos(prob,freq_expr, \
                      half_freq_expr, \
                      freq_ampl, \
                      cosvar,sinvar,
                      normalize=False):
  params = {
    'P0': 1.0,
    'V0' :0.0,
    'D0' :0.0,
    'P': "%s" % cosvar,
    'V': "ddt%s" % cosvar,
    'D': "div%s" % sinvar,
    'one': 0.9999999
  }
  expr = "%s*(-{P})" % freq_expr
  V = parse_diffeq(expr, \
                  "V0",
                  ":b%s" % cosvar,
                  params)

  expr = "{one}*({V})"
  P = parse_diffeq(expr, \
                   "P0",
                   ":a%s" % cosvar,
                   params)


  if normalize:
    expr = "3.0*({V}-%s*{D})" % half_freq_expr
    D = parse_diffeq(expr, \
                    "D0",
                    ":a%s" % sinvar,
                    params)

    prob.set_interval(params['D'],-1.0,1.0)
    prob.bind(params['D'], D)
    negD = parse_fn("(-{D})",params)
  else:
    negD = parse_fn("(-{V})",params)

  prob.bind(params['P'], P)
  prob.bind(params['V'], V)
  prob.bind(sinvar, negD)
  base_bnd = params['P0']*1.0
  slack = 1.2
  prob.set_interval(params['P'],-1.0*slack,1.0*slack)
  prob.set_interval(params['V'], \
                    -1.0*freq_ampl*slack, \
                    1.0*freq_ampl*slack)


def build_cos(prob,freq_expr,freq_ampl,varname):
  params = {
    'P0': 1.0,
    'V0' :0.0,
    'P': "%s" % varname,
    'V': "ddt%s" % varname,
    'one': 0.9999999
  }
  expr = "%s*(-{P})" % freq_expr
  V = parse_diffeq(expr, \
                  "V0",
                  ":b%s" % varname,
                  params)

  expr = "{one}*({V})"
  P = parse_diffeq(expr, \
                   "P0",
                   ":a%s" % varname ,
                   params)


  prob.bind(params['P'], P)
  prob.bind(params['V'], V)
  slack = 1.2
  prob.set_interval(params['P'],-1.0*slack,1.0*slack)
  prob.set_interval(params['V'], \
                    -1.0*freq_ampl*slack, \
                    1.0*freq_ampl*slack)



def build_sin(prob,freq_expr,freq_ampl,varname, \
              make_sin=False):
  params = {
    'P0': 0.0,
    'V0' :1.0,
    'P': "%s" % varname,
    'V': "ddt%s" % varname,
    'one': 0.9999999
  }

  expr = "%s*(-{P})" % freq_expr
  V = parse_diffeq(expr, \
                   "V0",
                   ":a%s" % varname ,
                   params)
  expr = "{one}*({V})"
  P = parse_diffeq(expr, \
                  "P0",
                  ":b%s" % varname,
                  params)
  prob.bind(params['P'], P)
  prob.bind(params['V'], V)
  base_bnd = params['P0']*1.0
  prob.set_interval(params['P'],-1.0,1.0)
  prob.set_interval(params['V'], \
                    -1.0*freq_ampl, \
                    1.0*freq_ampl)

def execute():
  prob = MathProg("build-sin-and-cos")
  build_sin_and_cos(prob,"0.25","0.5", \
                    1.0, \
                    "COS","SIN")
  prob.compile()
  menv = menvs.get_math_env('t200')
  plot_diffeq(menv,prob)


if __name__ == "__main__":
  execute()


