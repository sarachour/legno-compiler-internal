if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))

from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import math
import bmark.menvs as menvs

# build the dynamical system program for legno
def legno_demo():
  # system parameters
  params = {
    'Y0':0.1,
    'Z':0.2
  }
  # create a new math program named demo
  prob = MathProg("demo")
  Y = parse_diffeq('{Z}+(-Y)', 'Y0', ':a', params)

  # bind the differential equation to the variable Y.
  prob.bind("Y",Y)

  # measure Y, name the measurement O
  prob.bind("O",op.Emit(op.Var('Y'), loc='A0'))
  prob.set_interval("Y",0.0,0.3)

  # compile benchmark
  prob.compile()
  menv = menvs.get_math_env('t20')
  prob.set_max_sim_time(20)

  return menv,prob

# execute the dynamical system.
def execute():
  menv,prob = legno_demo()
  print(prob)
  input("<press any key to continue>")
  plot_diffeq(menv,prob)


if __name__ == "__main__":
  execute()
