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

def model(degree,method="basic"):
    prob = MathProg("bpf-%d-%s" % (degree,method))

    lb,ub = autil.set_microphone(prob,"I","Z")
    ampl = max(abs(lb),abs(ub))
    cutoff_freq0 = 4000
    out0,model0 = autil.lpf("Z","A",method, \
                            cutoff_freq0,degree)

    autil.model_to_diffeqs(prob,model0,ampl)

    cutoff_freq1 = 2000
    out1,model1 = autil.lpf("Z","B",method, \
                            cutoff_freq1,degree)
    autil.model_to_diffeqs(prob,model1,ampl)

    out_expr = parse_fn("%s+(-%s)" % (out0,out1),{})
    prob.bind("C", out_expr)
    autil.measure_var(prob,"C","OUT")
    prob.compile()
    menv = autil.math_env(prob)
    return menv,prob
