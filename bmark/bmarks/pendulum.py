if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs


def model():
  prob = MathProg('pend')
  params = {
    'angvel0': -1.0,
    'angle0': 1.0,
    'k1':0.18,
    'k2':0.8
  }
  sin_fun = op.Func(['T'], op.Mult(op.Const(-1),op.Sin(op.Var('T'))))

  eqn = parse_diffeq('{k1}*(-angvel) + ({k2}*(sinAngle))',  \
               'angvel0', ':a', params)
  prob.bind('angvel',eqn)

  eqn = parse_diffeq('angvel','angle0', \
                     ':b', params)
  prob.bind('angle',eqn)

  prob.bind('sinAngle', \
            op.Call([op.Var('angle')], sin_fun))
  prob.bind('ANGLE', op.Emit(op.Var('angle')))

  prob.set_interval('angle', -1.8,1.8)
  prob.set_interval('angvel',-1.8,1.8)
  prob.compile()
  menv = menvs.get_math_env('t20')
  return menv,prob

def execute():
  menv,prob = model()
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute()
