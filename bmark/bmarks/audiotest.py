if __name__ == "__main__":
    raise Exception("cannot run reference simulation for physical signal")

from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs
import chip.units as units
import chip.hcdc.globals as glb

def model():
    prob = MathProg("audiotest")
    prob.bind('X', op.ExtVar("I",loc='E1'))
    prob.bind('O', op.Emit(
        op.Mult(
            op.Const(0.9999),
            op.Var("X")
        ),loc='A0'))

    prob.set_bandwidth("I",200*units.khz/glb.TIME_FREQUENCY)
    prob.set_interval("I",-0.25,0.25)
    prob.set_max_sim_time(2)
    prob.compile()
    menv = menvs.get_math_env('audio')
    return menv,prob

