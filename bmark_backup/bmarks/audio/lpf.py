if __name__ == "__main__":
    raise Exception("cannot run reference simulation for physical signal")

from lang.prog import MathProg
from lang.prog import MathEnv
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs
import chip.units as units
import chip.hcdc.globals as glb
import numpy as np
from bmark.bmarks.audio import audio_util as autil
from enum import Enum

'''
   y is filter, x is input
   tau is the filter time constant
   k is the gain

   y' = k/tau * x - 1/tau * y
'''

def model(degree,method="basic"):
    prob = MathProg("lpf-%d-%s" % (degree,method))

    lb,ub = autil.set_microphone(prob,"I","Z")
    cutoff_freq = 20000
    out,model = autil.lpf("Z","X",method, \
                          cutoff_freq,degree)

    autil.model_to_diffeqs(prob,model,1.0)
    autil.measure_var(prob,out,"OUT")
    menv = autil.math_env(prob)

    prob.compile()
    return menv,prob

