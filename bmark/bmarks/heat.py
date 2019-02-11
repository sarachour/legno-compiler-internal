if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs



def model(n):
  params = {
    'init_heat': 2.0,
    'ic': 0
  }

  prob = MathProg('heat1d-g%d' % n)
  for i in range(0,n):
    params['curr'] = "u%d" % (i)
    if i > 0 and i < n-1:
      params['prev'] = "u%d" % (i-1)
      params['next'] = "u%d" % (i+1)
      eqn=parse_diffeq('{prev} - 2*{curr} + {next}', 'ic', \
                   ':q%d' % i, params)
    elif i > 0:
      assert(i == n-1)
      params['prev'] = "u%d" % (i-1)
      eqn=parse_diffeq('{prev} - 2*{curr}', 'init_heat', \
                   ':q%d' % i, params)
    elif i < n-1:
      params['next'] = "u%d" % (i+1)
      eqn=parse_diffeq('{next}-2*{curr}', 'ic', \
                   ':q%d' % i, params)
    else:
      raise Exception("???")

    coeff = 1/(2.0*n)
    prob.bind(params['curr'], op.Mult(op.Const(coeff),eqn))
    prob.set_interval(params['curr'],-2,2)

  #prob.compile()
  menv = menvs.get_math_env('t20')
  return menv,prob

def execute():
  menv,prob = model()
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute()
