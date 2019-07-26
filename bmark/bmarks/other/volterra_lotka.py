if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))


from bmark.bmarks.common import *
from lang.prog import MathProg
from ops import op, opparse
import bmark.menvs as menvs

def model(tag='simple'):
    prob = MathProg("lotka-%s" % tag)
    params = {
      'rabbit_spawn':0.01,
      'fox_death': 0.2,
      'rabbit_kill': 0.1,
      'fox_reproduce': 0.20,
      "fox_init": 1.0,
      "rabbit_init": 5.0,
      'one':0.999999
    }
    params['fox_spawn'] = params['fox_reproduce']*params['rabbit_kill']

    X = parse_diffeq('{rabbit_spawn}*RABBIT + {rabbit_kill}*(-FIGHT)', \
                     "rabbit_init",":a",params)
    Y = parse_diffeq('{fox_spawn}*FIGHT+ {fox_death}*(-FOX)', \
                     "fox_init",":b",params)
    Z = parse_fn("FOX*({one}*RABBIT)",params)
    prob.bind("FIGHT",Z)
    prob.bind("RABBIT",X)
    prob.bind("FOX",Y)
    measure_var(prob,"RABBIT", "PREY")

    rabbit_ival = 8.0
    fox_ival = 2.0
    prob.set_interval("RABBIT",0,rabbit_ival)
    prob.set_interval("FOX",0,fox_ival)
    prob.set_interval("FIGHT",0,5.5)
    prob.set_max_sim_time(50)
    prob.compile()
    menv = menvs.get_math_env('t50')
    return menv,prob



def execute():
  menv,prob = model()
  plot_diffeq(menv,prob)


if __name__ == "__main__":
  execute()
