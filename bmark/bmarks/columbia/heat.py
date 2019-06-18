if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs

def emit(v):
  return op.Emit(op.Mult(op.Const(0.99999), v),loc="A0")


def model(n,obs_idx):
  params = {
    'init_heat': 1.0,
    'ic': 0,
    #'coeff': 1/(2.0*n)
    'coeff': 0.9999999
  }
  params['2coeff'] = params['coeff']*2

  prob = MathProg('heat1d-g%d' % n)
  prob.set_digital_snr(10.0)
  prob.set_analog_snr(4)
  for i in range(0,n):
    params['curr'] = "u%d" % (i)
    if i > 0 and i < n-1:
      params['prev'] = "u%d" % (i-1)
      params['next'] = "u%d" % (i+1)
      eqn=parse_diffeq('{coeff}*{prev} + {2coeff}*(-{curr}) + {coeff}*{next}',\
                       'ic', \
                       ':q%d' % i, params)
    elif i > 0:
      assert(i == n-1)
      params['prev'] = "u%d" % (i-1)
      eqn=parse_diffeq('{coeff}*{prev} + {2coeff}*(-{curr})', \
                       'init_heat', \
                       ':q%d' % i, params)
    elif i < n-1:
      params['next'] = "u%d" % (i+1)
      eqn=parse_diffeq('{coeff}*{next}+{2coeff}*(-{curr})', 'ic', \
                   ':q%d' % i, params)
    else:
      raise Exception("???")

    prob.bind(params['curr'], eqn)
    prob.set_interval(params['curr'],0,params['init_heat'])

  prob.bind("POINT", emit(op.Var("u%d" % obs_idx)))
  prob.set_max_sim_time(200)
  prob.compile()
  menv = menvs.get_math_env('t200')
  return menv,prob

def execute(n,o):
  menv,prob = model(n,o)
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute(2,1)
  execute(4,2)
  execute(8,0)
  execute(16,13)
