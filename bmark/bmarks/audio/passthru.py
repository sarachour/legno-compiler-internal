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

def model():
    prob = MathProg("aud-passthru")

    bw = 20*units.khz/glb.TIME_FREQUENCY
    ampl = 1.0

    prob.set_bandwidth("I",bw)
    prob.set_interval("I",-ampl,ampl)

    expr = op.Mult(op.Var('X'),op.Const(0.9999))
    prob.bind('X', op.ExtVar("I",loc='E1'))
    prob.bind('OUT',op.Emit(expr, loc='A0'))
    time = 0.1
    prob.set_max_sim_time(time*glb.TIME_FREQUENCY)
    prob.compile()

    menv = MathEnv('audenv');
    menv.set_sim_time(time*glb.TIME_FREQUENCY)
    menv.set_input_time(time*glb.TIME_FREQUENCY)
    return menv,prob

