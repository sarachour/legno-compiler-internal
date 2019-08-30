if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs


def model():
    prob = MathProg("cosc")
    params = {
      'V0': -2,
      'P0': 9,
      'one':0.9999
    }
    V = parse_diffeq('0.22*(-V) + 0.84*(-P)', 'V0', ':a', params)
    P = parse_diffeq('{one}*V', 'P0', ':b', params)

    prob.bind('V', V)
    prob.bind('P', P)
    prob.bind('Loc', op.Emit(
      op.Mult(op.Const(params['one']),op.Var('P')),
      loc="A0"
    ))
    prob.set_interval("V",-10,10)
    prob.set_interval("P",-10,15)
    prob.set_interval("Loc",-10,15)
    prob.set_max_sim_time(20)
    prob.compile()
    menv = menvs.get_math_env('t20')
    return menv,prob

def execute():
  menv,prob = model()
  plot_diffeq(menv,prob)


if __name__ == "__main__":
  execute()
