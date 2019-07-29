if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs


def model(n,obs_idx,with_gain=False):
  #h = 1.0/(n-1)
  params = {
    'init_heat': 2.0,
    'ic': 0,
    'one':0.99999
  }

  if with_gain:
    prob = MathProg('heat1d-g%d-wg' % n)
  else:
    prob = MathProg('heat1d-g%d' % n)

  for i in range(1,n):
    params['curr'] = "u%d" % (i)
    params['prev'] = "u%d" % (i-1) if i-1 >= 1 else 0.0
    params['next'] = "u%d" % (i+1) if i+1 < n else params['init_heat']
    if with_gain:
      eqn=parse_diffeq('{one}*({prev} +(-{curr}) +(-{curr})+ {next})',\
                       'ic', \
                       ':q%d' % i, params)
    else:
      eqn=parse_diffeq('({prev} +(-{curr}) +(-{curr})+ {next})',\
                        'ic', \
                        ':q%d' % i, params)
    prob.bind(params['curr'], eqn)
    prob.set_interval(params['curr'],0,params['init_heat'])

  measure_var(prob,"u%d" % obs_idx,'POINT')
  prob.set_max_sim_time(200)
  prob.compile()
  menv = menvs.get_math_env('t200')
  return menv,prob

def execute(n,o):
  menv,prob = model(n,o)
  plot_diffeq(menv,prob)


if __name__ == "__main__":
  execute(4,2)
  execute(8,7)
  execute(16,15)
