from lang.prog import MathProg
from lang.prog import MathEnv
import bmark.bmarks.audio.audio_util as autil
from bmark.bmarks.common import *
from ops import op, opparse
import bmark.menvs as menvs


def model():
    # y'' - u(1-y^2)*y'+y = 0
    # separated
    # y1' = y2
    # y2' = u*(1-y1*y1)*y2 - y1
    prob = MathProg("forced-vanderpol")

    # i reduced mu from 0.2 to 0.05 so that the interval of Y' is between
    # [-2,2]

    rel_time = 0.05
    mu = 0.2
    params = {
      'mu': rel_time*mu,
      'Y0': 0.0,
      'X0': -0.5,
      'tc':1.0*rel_time
    }
    #Y = parse_diffeq('(Y*{mu}*(1.0-{onehack}*X*X) - {onehack}*X)','Y0',':v',params)
    #X = parse_diffeq('{onehack}*Y','X0',':u',params)

    lb,ub = autil.set_microphone(prob,"I","Z")
    Y = parse_diffeq('{tc}*Z+Y*{mu}*(1.0+(-X)*X)+{tc}*(-X)', \
                     'Y0',':v',params)
    X = parse_diffeq('{tc}*Y','X0',':u',params)

    prob.bind("Y",Y)
    prob.bind("X",X)
    prob.bind("OUTX",op.Emit(op.Var("X"), loc="A0"))
    prob.set_interval("X",-2.0,2.0)
    prob.set_interval("Y",-2.0,2.0)
    prob.set_interval("OUTX",-2.0,2.0)
    prob.compile()
    menv = autil.math_env(prob,0.1)
    return menv,prob

def execute():
  menv,prob = model()
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute()
