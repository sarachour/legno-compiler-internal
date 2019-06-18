if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs


def model():
    prob = MathProg("cosc")
    prob.set_digital_snr(10.0)
    dy2 = op.Add(
        op.Mult(op.Var("dy1"),op.Const(-0.2)),
        op.Mult(op.Var("y"),op.Const(-0.8))
    )
    dy1 = op.Integ(dy2, op.Const(-2),":z")
    y = op.Integ(op.Var("dy1"), op.Const(9),":w")

    params = {
      'V0': -2,
      'P0': 9,
      'one':0.9999
    }
    V = parse_diffeq('0.22*(-V) + 0.84*(-P)', 'P0', ':a', params)
    P = parse_diffeq('{one}*V', 'P0', ':b', params)

    prob.bind('V', V)
    prob.bind('P', P)
    prob.bind('Loc', op.Emit(
      op.Mult(op.Const(1.0),op.Var('P')),
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
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute()
