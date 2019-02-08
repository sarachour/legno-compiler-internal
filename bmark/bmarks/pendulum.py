from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs


def model():
  prob = MathProg('pend')
  params {
    'angvel': -1.0,
    'angle': 1.0,
  }
  sin_fun = op.Func(['T'], op.Sin(op.Var('T')))

  parse_diffeq('-{k1}*angvel - {k2}*sinAngle',  \
               'angvel0', ':a', params)
  parse_diffeq('angvel','angle0', ':b', params)
  prob.bind('sinAngle', \
            op.Call([op.Var('angle', sin_fun)]))
  prob.set_interval('angle', -1,1)
  prob.set_interval('angvel',-1,1)
  return prob
